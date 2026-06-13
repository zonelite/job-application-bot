import imaplib
import logging
import re
from typing import List, Tuple, Optional
from email.parser import BytesParser
from datetime import datetime, timedelta

from config.settings import (
    EMAIL_PROVIDER,
    IMAP_EMAIL,
    IMAP_PASSWORD,
    IMAP_SERVER,
    IMAP_PORT,
)

logger = logging.getLogger(__name__)


class EmailMonitor:
    """Monitor Gmail or Outlook for application responses"""

    def __init__(self):
        self.email = IMAP_EMAIL
        self.password = IMAP_PASSWORD
        self.imap_server = IMAP_SERVER
        self.imap_port = IMAP_PORT
        self.provider = EMAIL_PROVIDER
        logger.info(f"Initialized EmailMonitor for {self.provider.upper()}")

    def connect(self) -> Optional[imaplib.IMAP4_SSL]:
        """Connect to email provider IMAP"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email, self.password)
            logger.info(f"Connected to {self.provider.upper()} IMAP")
            return mail
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP Error connecting to {self.provider}: {e}")
            if "AUTHENTICATIONFAILED" in str(e):
                logger.error(
                    f"Authentication failed. Make sure you're using an App Password, not your regular password."
                )
            return None
        except Exception as e:
            logger.error(f"Error connecting to {self.provider} IMAP: {e}")
            return None

    def get_recent_emails(self, days: int = 7) -> List[Tuple[str, str, str]]:
        """Get recent emails from last N days

        Returns:
            List of (subject, sender, body) tuples
        """
        mail = self.connect()
        if not mail:
            return []

        try:
            mail.select("INBOX")

            # Search for emails from last N days
            date_since = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
            _, message_ids = mail.search(None, f"SINCE {date_since}")

            emails = []
            for msg_id in message_ids[0].split():
                try:
                    _, msg_data = mail.fetch(msg_id, "(RFC822)")
                    msg = BytesParser().parsebytes(msg_data[0][1])

                    subject = msg.get("Subject", "")
                    sender = msg.get("From", "")
                    body = self._extract_body(msg)

                    emails.append((subject, sender, body))
                except Exception as e:
                    logger.warning(f"Error parsing email: {e}")
                    continue

            logger.info(f"Retrieved {len(emails)} emails from last {days} days")
            return emails

        except Exception as e:
            logger.error(f"Error retrieving emails: {e}")
            return []
        finally:
            try:
                mail.close()
                mail.logout()
            except:
                pass

    def parse_application_status(
        self, emails: List[Tuple[str, str, str]]
    ) -> List[dict]:
        """Parse emails to extract application status

        Returns:
            List of dicts with status information
        """
        statuses = []

        for subject, sender, body in emails:
            status = self._classify_email(subject, body)
            if status["type"] != "unknown":
                statuses.append(
                    {
                        "sender": sender,
                        "subject": subject,
                        "status_type": status["type"],
                        "confidence": status["confidence"],
                    }
                )

        return statuses

    def _extract_body(self, msg) -> str:
        """Extract text body from email"""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode(
                            "utf-8", errors="ignore"
                        )
                        break
                    except Exception as e:
                        logger.debug(f"Error extracting body: {e}")
                        continue
        else:
            try:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            except Exception as e:
                logger.debug(f"Error extracting body: {e}")
                body = msg.get_payload()

        return body[:2000]  # Limit to first 2000 chars for processing

    def _classify_email(self, subject: str, body: str) -> dict:
        """Classify email as rejection, interview, etc."""
        text = f"{subject} {body}".lower()

        # Rejection keywords
        if any(
            kw in text
            for kw in [
                "reject",
                "not selected",
                "unsuccessful",
                "not move forward",
                "decline",
                "not proceeding",
                "position filled",
                "not advancing",
            ]
        ):
            return {"type": "rejected", "confidence": 0.95}

        # Interview keywords
        if any(
            kw in text
            for kw in [
                "interview",
                "next step",
                "move forward",
                "schedule",
                "screening call",
                "technical round",
                "phone screen",
                "interview scheduled",
                "interview invitation",
            ]
        ):
            return {"type": "interviewed", "confidence": 0.90}

        # Confirmation keywords
        if any(
            kw in text
            for kw in [
                "received",
                "acknowledge",
                "submit",
                "applied",
                "application received",
                "thank you for applying",
            ]
        ):
            return {"type": "submitted", "confidence": 0.70}

        return {"type": "unknown", "confidence": 0.0}
