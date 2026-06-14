# Documentation for Job Application Bot

Complete guides for setting up and using the job application bot.

## Quick Links

- **[README.md](README.md)** - Project overview and features
- **[SETUP.md](SETUP.md)** - Step-by-step installation guide
- **[EMAIL_SETUP.md](EMAIL_SETUP.md)** - Gmail vs Outlook configuration
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture details

## Getting Started

### New User?
1. Start with [SETUP.md](SETUP.md) - 5 minute setup
2. Then read [EMAIL_SETUP.md](EMAIL_SETUP.md) - Choose Gmail or Outlook
3. Finally [README.md](README.md) - Full feature documentation

### Having Issues?
1. Check [EMAIL_SETUP.md](EMAIL_SETUP.md) troubleshooting section
2. Enable DEBUG logging in `.env`
3. Check `logs/job_bot.log` for detailed error messages
4. Open an issue with logs attached

## File Structure

```
docs/
├── README.md          # Main documentation
├── SETUP.md          # Installation steps
├── EMAIL_SETUP.md    # Email provider setup
└── ARCHITECTURE.md   # Technical details
```

## Core Components

### Config (`config/settings.py`)
- Environment variable loading
- Supports both Gmail and Outlook
- Database and cache paths

### Database (`database/models.py`)
- SQLite models for jobs, applications, resumes
- CRUD operations
- Statistics queries

### Scrapers (`scrapers/`)
- HiringCafe RSS feed parser
- Extensible for other job sources

### Resume (`resume/customizer.py`)
- Ollama LLM integration
- Keyword extraction
- Smart caching with similarity matching

### Applier (`applier/`)
- Workday, Greenhouse, Lever ATS adapters
- Playwright-based browser automation
- Error handling and retries

### Email (`monitoring/email_monitor.py`)
- Gmail and Outlook IMAP support
- Email classification (rejection, interview, submitted)
- Confidence scoring

### Security (`security/credentials.py`)
- Fernet encryption for local credentials
- No cloud dependency

### Orchestrator (`orchestrator.py`)
- Main application loop
- Job scraping → resume customization → application submission
- Error handling and logging

### Dashboard (`dashboard.py`)
- Streamlit web interface
- Statistics and application history
- Email monitoring
- User profile setup

### Scheduler (`scheduler.py`)
- Background job scheduling
- Configurable intervals (default: every 6 hours)

## Configuration

All configuration in `.env` file:

```bash
# Email Provider (gmail or outlook)
EMAIL_PROVIDER=gmail

# Gmail (if using Gmail)
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# Outlook (if using Outlook)
OUTLOOK_EMAIL=your-email@outlook.com
OUTLOOK_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Application behavior
MAX_APPLICATIONS_PER_DAY=5
RESUME_CACHE_SIMILARITY_THRESHOLD=0.75
APP_LOG_LEVEL=INFO
```

## Usage Examples

### One-time run
```bash
python orchestrator.py
```

### Scheduled (every 6 hours)
```bash
python scheduler.py
```

### Web dashboard
```bash
streamlit run dashboard.py
```

## Logging

All activity logged to `logs/job_bot.log`:

```
2024-06-13 10:23:45,123 - orchestrator - INFO - Starting full job application cycle
2024-06-13 10:23:47,456 - scrapers.hiringcafe_scraper - INFO - Scraped 15 jobs from HiringCafe
2024-06-13 10:23:52,789 - resume.customizer - INFO - Extracted keywords: [...]
2024-06-13 10:24:05,234 - applier.applier - INFO - Successfully applied to job
```

## Database Schema

SQLite database at `data/job_bot.db` contains:

- `listings` - Job postings scraped from sources
- `applications` - Records of submitted applications
- `resume_versions` - Resume variants used for each application

## Troubleshooting

### Email Issues
See [EMAIL_SETUP.md](EMAIL_SETUP.md) troubleshooting section

### Ollama Connection
```bash
# Start Ollama
ollama serve

# In another terminal, pull model
ollama pull mistral

# Test connection
curl http://localhost:11434/api/tags
```

### Resume Customization Slow
Switch to Mistral model (faster than Llama)

### Database Locked
Close other connections or restart the bot

## Performance Tips

1. **Use Mistral 7B** - Faster than larger models
2. **Increase cache threshold** - Reuse more cached resumes
3. **Reduce max applications** - Faster job finding
4. **Run during off-peak** - Avoid rate limiting

## Security

✅ Credentials encrypted locally with Fernet  
✅ App Passwords for email (limited scope)  
✅ No cloud dependency  
✅ Logs exclude sensitive data  
✅ .gitignore prevents credential leaks  

## Contributing

Feel free to improve:
- Job filtering logic
- More ATS adapters
- Email classification
- Performance optimizations

## Support

For issues:
1. Check relevant doc (README, SETUP, EMAIL_SETUP)
2. Enable DEBUG logging
3. Check logs in `logs/job_bot.log`
4. Open an issue with logs attached

---

**Built for students with zero budget. Made with ❤️ for automation enthusiasts.**
