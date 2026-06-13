import logging
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import List

from config.settings import (
    MAX_APPLICATIONS_PER_DAY,
    APP_LOG_LEVEL,
    LOGS_DIR,
)
from database.models import Database, Job, Application, ResumeVersion
from scrapers import HiringCafeScraper
from resume import ResumeCustomizer
from applier import ApplicationEngine
from monitoring import EmailMonitor
from security import CredentialManager

# Setup logging
logging.basicConfig(
    level=getattr(logging, APP_LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "job_bot.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class JobApplicationOrchestrator:
    """Main orchestrator for job application automation"""

    def __init__(self, db: Database):
        self.db = db
        self.scraper = HiringCafeScraper()
        self.customizer = ResumeCustomizer()
        self.applier = ApplicationEngine()
        self.email_monitor = EmailMonitor()
        self.credentials = CredentialManager()
        self.master_resume = self._load_master_resume()

    def _load_master_resume(self) -> str:
        """Load master resume from file"""
        resume_path = Path("data/master_resume.md")
        if resume_path.exists():
            with open(resume_path, "r") as f:
                return f.read()
        logger.warning("Master resume not found at data/master_resume.md")
        return ""

    async def run_full_cycle(self):
        """Run complete job application cycle"""
        logger.info("Starting full job application cycle")

        try:
            # 1. Scrape for new jobs
            logger.info("Step 1: Scraping for new jobs")
            new_jobs = await self.scrape_jobs()
            logger.info(f"Found {len(new_jobs)} new jobs")

            # 2. Filter and process jobs
            logger.info("Step 2: Processing jobs")
            jobs_to_apply = await self.filter_jobs(new_jobs)
            logger.info(f"Filtered to {len(jobs_to_apply)} jobs to apply")

            # 3. Apply to jobs (respecting daily limit)
            logger.info("Step 3: Applying to jobs")
            applications_today = self.db.get_applications_today()
            remaining_quota = MAX_APPLICATIONS_PER_DAY - len(applications_today)

            if remaining_quota > 0:
                jobs_to_apply = jobs_to_apply[:remaining_quota]
                await self.apply_to_jobs(jobs_to_apply)
            else:
                logger.info(
                    f"Daily quota reached ({MAX_APPLICATIONS_PER_DAY} applications)"
                )

            # 4. Monitor emails for responses
            logger.info("Step 4: Monitoring email responses")
            self.check_email_responses()

            logger.info("Full cycle completed successfully")

        except Exception as e:
            logger.error(f"Error in full cycle: {e}", exc_info=True)
        finally:
            await self.cleanup()

    async def scrape_jobs(self) -> List[Job]:
        """Scrape jobs from all sources"""
        try:
            hiringcafe_jobs = await self.scraper.scrape()
            logger.info(f"Scraped {len(hiringcafe_jobs)} jobs from HiringCafe")

            # Add to database
            for job in hiringcafe_jobs:
                try:
                    self.db.add_listing(job)
                except Exception as e:
                    logger.debug(f"Job already in database: {e}")

            return hiringcafe_jobs
        except Exception as e:
            logger.error(f"Error scraping jobs: {e}")
            return []

    async def filter_jobs(self, jobs: List[Job]) -> List[Job]:
        """Filter jobs based on criteria"""
        filtered = []
        for job in jobs:
            # Simple filtering - can be expanded with more rules
            if self._is_relevant_job(job):
                filtered.append(job)
        return filtered

    def _is_relevant_job(self, job: Job) -> bool:
        """Check if job is relevant"""
        # TODO: Implement job filtering logic
        # Can use keywords, company filters, etc.
        return True

    async def apply_to_jobs(self, jobs: List[Job]):
        """Apply to selected jobs"""
        # Load user credentials
        user_creds = self.credentials.get_credentials("user_profile")
        if not user_creds:
            logger.error("User credentials not found. Set them up first.")
            return

        for job in jobs:
            try:
                logger.info(f"Processing job: {job.title} at {job.company}")

                # Customize resume
                customized_resume, keywords = await self.customizer.customize_resume(
                    self.master_resume, job.description_text
                )

                # Save customized resume to temp file
                resume_path = self._save_temp_resume(customized_resume)

                # Detect ATS type (simplified - in real world, this would be more sophisticated)
                ats_type = self._detect_ats_type(job.url)

                # Apply to job
                success = await self.applier.apply_to_job(
                    job_url=job.url,
                    ats_type=ats_type,
                    form_data={
                        "first_name": user_creds.get("first_name", ""),
                        "last_name": user_creds.get("last_name", ""),
                        "email": user_creds.get("email", ""),
                        "phone": user_creds.get("phone", ""),
                    },
                    resume_path=str(resume_path),
                )

                if success:
                    # Record application
                    app = Application(
                        job_id=job.id or 0,
                        job_title=job.title,
                        company=job.company,
                        url=job.url,
                        date_applied=datetime.now().isoformat(),
                        status="submitted",
                        ats_type=ats_type,
                    )
                    app_id = self.db.add_application(app)

                    # Record resume version
                    resume_ver = ResumeVersion(
                        application_id=app_id,
                        resume_text_markdown=customized_resume,
                        keywords_used=",".join(keywords),
                    )
                    self.db.add_resume_version(resume_ver)

                    logger.info(f"Successfully applied to {job.title}")
                else:
                    logger.warning(f"Failed to apply to {job.title}")

                # Be polite - don't apply too fast
                await asyncio.sleep(3)

            except Exception as e:
                logger.error(f"Error applying to {job.title}: {e}", exc_info=True)

    def _save_temp_resume(self, resume_content: str) -> Path:
        """Save customized resume to temporary file"""
        temp_path = Path(f"data/resume_{datetime.now().timestamp()}.md")
        with open(temp_path, "w") as f:
            f.write(resume_content)
        return temp_path

    def _detect_ats_type(self, url: str) -> str:
        """Detect ATS type from URL"""
        url_lower = url.lower()
        if "workday" in url_lower:
            return "workday"
        elif "greenhouse" in url_lower:
            return "greenhouse"
        elif "lever" in url_lower:
            return "lever"
        else:
            # Default to workday
            return "workday"

    def check_email_responses(self):
        """Check email for application responses"""
        try:
            emails = self.email_monitor.get_recent_emails(days=7)
            statuses = self.email_monitor.parse_application_status(emails)

            for status in statuses:
                logger.info(
                    f"Email from {status['sender']}: {status['status_type']} (confidence: {status['confidence']})"
                )
                # TODO: Match with applications and update status

        except Exception as e:
            logger.error(f"Error checking emails: {e}")

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources")
        await self.scraper.close()
        await self.customizer.close()


async def main():
    """Main entry point"""
    from config.settings import DB_PATH

    db = Database(DB_PATH)
    orchestrator = JobApplicationOrchestrator(db)
    await orchestrator.run_full_cycle()


if __name__ == "__main__":
    asyncio.run(main())
