import schedule
import asyncio
import logging
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import DB_PATH, SCRAPE_INTERVAL_HOURS
from database.models import Database
from orchestrator import JobApplicationOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_job_cycle():
    """Run the job application cycle"""
    logger.info("Scheduled job cycle starting...")
    db = Database(DB_PATH)
    orchestrator = JobApplicationOrchestrator(db)
    asyncio.run(orchestrator.run_full_cycle())
    logger.info("Scheduled job cycle completed")


def main():
    """Main scheduler loop"""
    logger.info("Job Application Bot Scheduler started")
    
    # Schedule job cycle every N hours
    schedule.every(SCRAPE_INTERVAL_HOURS).hours.do(run_job_cycle)
    
    # Run initial cycle
    logger.info("Running initial job cycle...")
    run_job_cycle()
    
    # Keep scheduler running
    logger.info(f"Next cycle scheduled in {SCRAPE_INTERVAL_HOURS} hours")
    while True:
        schedule.run_pending()
        import time
        time.sleep(60)  # Check schedule every minute


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
