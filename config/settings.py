import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
DB_PATH = DATA_DIR / "job_bot.db"
CREDENTIALS_PATH = DATA_DIR / "credentials.json"
RESUME_CACHE_PATH = DATA_DIR / "resume_cache.json"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Email Configuration
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "gmail").lower()  # gmail or outlook

# Gmail Configuration
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
GMAIL_IMAP_SERVER = "imap.gmail.com"
GMAIL_IMAP_PORT = 993

# Outlook Configuration (works with outlook.com, hotmail.com, live.com)
OUTLOOK_EMAIL = os.getenv("OUTLOOK_EMAIL")
OUTLOOK_APP_PASSWORD = os.getenv("OUTLOOK_APP_PASSWORD")
OUTLOOK_IMAP_SERVER = "outlook.office365.com"
OUTLOOK_IMAP_PORT = 993

# Use appropriate credentials based on provider
if EMAIL_PROVIDER == "outlook":
    IMAP_EMAIL = OUTLOOK_EMAIL
    IMAP_PASSWORD = OUTLOOK_APP_PASSWORD
    IMAP_SERVER = OUTLOOK_IMAP_SERVER
    IMAP_PORT = OUTLOOK_IMAP_PORT
else:  # Default to gmail
    IMAP_EMAIL = GMAIL_EMAIL
    IMAP_PASSWORD = GMAIL_APP_PASSWORD
    IMAP_SERVER = GMAIL_IMAP_SERVER
    IMAP_PORT = GMAIL_IMAP_PORT

# LLM Configuration - Choose: "ollama" or "groq"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

# Ollama Configuration (local)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# Groq Cloud Configuration (free, fast API)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")  # Free models available

# Set LLM credentials based on provider
if LLM_PROVIDER == "groq":
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY required when LLM_PROVIDER=groq. Get it from https://console.groq.com")
else:
    # Ollama is the fallback
    LLM_PROVIDER = "ollama"

# Application Settings
MAX_APPLICATIONS_PER_DAY = int(os.getenv("MAX_APPLICATIONS_PER_DAY", 5))
RESUME_CACHE_SIMILARITY_THRESHOLD = float(
    os.getenv("RESUME_CACHE_SIMILARITY_THRESHOLD", 0.75)
)
APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO")

# Playwright
HEADLESS_MODE = True
BROWSER_TIMEOUT = 30000  # 30 seconds
NAVIGATION_TIMEOUT = 30000

# Scraper
HIRINGCAFE_RSS_URL = "https://hiringcafe.com/feed/"
SCRAPE_INTERVAL_HOURS = 6
