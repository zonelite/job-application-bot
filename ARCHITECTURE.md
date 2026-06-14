# Technical Architecture - Job Application Bot

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Job Application Bot                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │   Scraper    │     │  Customizer  │     │   Applier    │ │
│  │ (HiringCafe) │────→│ (Ollama LLM) │────→│ (Playwright) │ │
│  │    RSS       │     │ (Resume)     │     │ (Multi-ATS)  │ │
│  └──────────────┘     └──────────────┘     └──────────────┘ │
│       │                     │                     │           │
│       ↓                     ↓                     ↓           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │             SQLite Database                         │   │
│  │  ├─ listings       (job postings)                   │   │
│  │  ├─ applications   (submission records)             │   │
│  │  └─ resume_versions (customized resumes)           │   │
│  └──────────────────────────────────────────────────────┘   │
│       │                                                       │
│       ↓                                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Email Monitor (Gmail/Outlook)               │   │
│  │    ├─ Email classification                          │   │
│  │    └─ Status detection (interview/rejection)        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Orchestrator / Scheduler / Dashboard               │   │
│  │    ├─ Full cycle automation                         │   │
│  │    ├─ Background scheduling                         │   │
│  │    └─ Web UI (Streamlit)                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Scraper (HiringCafe)

**File:** `scrapers/hiringcafe_scraper.py`

**Responsibilities:**
- Fetch RSS feed from HiringCafe
- Parse job entries
- Extract: title, company, URL, description
- Handle network errors gracefully

**Flow:**
```
Fetch RSS → Parse entries → Extract job data → Return Job objects
```

**Key Features:**
- Async HTTP client (httpx)
- BeautifulSoup for HTML cleaning
- 20 latest jobs per scrape
- Error logging

### 2. Resume Customizer (Ollama LLM)

**File:** `resume/customizer.py`

**Responsibilities:**
- Connect to local Ollama instance
- Extract keywords from job description
- Customize resume with keywords
- Cache similar resumes (avoid regeneration)

**Flow:**
```
Job Description → Extract 10 Keywords → Customize Resume → Cache
                                              ↓
                                    Check Cache First
                                    (similarity matching)
```

**Caching Logic:**
- Hash job descriptions
- Calculate Jaccard similarity between descriptions
- Reuse resume if similarity > threshold (default: 0.75)
- Store cache in JSON file

**LLM Prompts:**
```
1. Extract Keywords Prompt:
   "Extract 10 most important keywords from job description"
   Returns: keyword list

2. Customize Resume Prompt:
   "Rewrite resume to naturally include keywords"
   Input: master_resume, job_description, keywords
   Output: customized_resume (markdown)
```

### 3. Application Engine (Playwright)

**File:** `applier/applier.py` + `applier/ats_adapters.py`

**Responsibilities:**
- Launch browser with Playwright
- Navigate to job application
- Delegate to appropriate ATS adapter
- Fill form fields
- Upload resume
- Submit application

**Flow:**
```
Start Browser → Navigate to URL → Detect ATS Type → Fill Form → Submit
```

**Supported ATS Systems:**

#### Workday
```python
Selectors:
  first_name: input[data-fieldname*='firstName']
  last_name:  input[data-fieldname*='lastName']
  email:      input[type='email']
  phone:      input[type='tel']
  resume:     input[type='file']
  submit:     button:has-text('Submit')
```

#### Greenhouse
```python
Selectors:
  first_name: input[name='first_name']
  last_name:  input[name='last_name']
  email:      input[name='email']
  phone:      input[name='phone']
  resume:     input[type='file']
  submit:     button:has-text('Apply')
```

#### Lever
```python
Selectors:
  name:       input[name='name']
  email:      input[name='email']
  phone:      input[name='phone']
  resume:     input[type='file']
  submit:     button:has-text('Apply')
```

### 4. Email Monitor (Gmail/Outlook IMAP)

**File:** `monitoring/email_monitor.py`

**Responsibilities:**
- Connect to email provider IMAP
- Fetch recent emails (last N days)
- Classify emails by status
- Extract sender and subject

**Flow:**
```
Connect to IMAP → Search last 7 days → Parse emails → Classify → Return statuses
```

**Email Classification:**
```python
REJECTION (95% confidence):
  Keywords: reject, unsuccessful, not selected, position filled

INTERVIEW (90% confidence):
  Keywords: interview, next step, screening call, technical round

SUBMITTED (70% confidence):
  Keywords: received, acknowledge, thank you for applying
```

**Provider Support:**
- **Gmail:** `imap.gmail.com:993`
- **Outlook:** `outlook.office365.com:993`

### 5. Database Layer (SQLite)

**File:** `database/models.py`

**Schema:**

```sql
-- Job listings
CREATE TABLE listings (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    source TEXT DEFAULT 'hiringcafe',
    description_text TEXT,
    date_found TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- Applications submitted
CREATE TABLE applications (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL,
    job_title TEXT NOT NULL,
    company TEXT NOT NULL,
    url TEXT NOT NULL,
    date_applied TEXT,
    status TEXT DEFAULT 'pending',  -- pending, submitted, rejected, interviewed
    ats_type TEXT,  -- workday, greenhouse, lever
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES listings(id)
)

-- Resume versions
CREATE TABLE resume_versions (
    id INTEGER PRIMARY KEY,
    application_id INTEGER NOT NULL,
    resume_text_markdown TEXT NOT NULL,
    keywords_used TEXT,  -- JSON array
    job_description_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id)
)
```

**Operations:**
- `add_listing(job)` - Insert new job
- `add_application(app)` - Record application
- `add_resume_version(resume)` - Store customized resume
- `get_applications_today()` - Fetch today's applications
- `get_application_stats()` - Calculate metrics
- `update_application_status(app_id, status)` - Update status

### 6. Security (Credentials)

**File:** `security/credentials.py`

**Responsibilities:**
- Encrypt credentials locally
- Store user profile safely
- Decrypt on demand

**Flow:**
```
User Credentials → Fernet Encryption → Store in JSON → Decrypt on use
```

**Encryption:**
- Algorithm: Fernet (symmetric)
- Key: Generated or from ENCRYPTION_KEY env var
- Storage: `data/credentials.json`

### 7. Orchestrator (Main Loop)

**File:** `orchestrator.py`

**Responsibilities:**
- Coordinate all components
- Implement full application cycle
- Handle errors and cleanup
- Respect daily rate limits

**Cycle Steps:**
```
1. Scrape jobs (HiringCafe RSS)
2. Add to database
3. Filter relevant jobs
4. Customize resume for each
5. Apply to job (Playwright + ATS adapter)
6. Record application in database
7. Store resume version
8. Check email for responses
9. Update application status
```

**Error Handling:**
- Try-catch on each step
- Log all errors
- Continue on partial failures
- Cleanup resources

### 8. Scheduler

**File:** `scheduler.py`

**Responsibilities:**
- Run orchestrator at intervals
- Background daemon
- Configurable schedule

**Usage:**
```bash
python scheduler.py
# Runs orchestrator every 6 hours (configurable)
```

### 9. Dashboard (Streamlit)

**File:** `dashboard.py`

**Pages:**
1. **Stats Tab**
   - Total applications
   - Success rate (interviewed / total)
   - Today's applications
   - Key metrics

2. **Applications Tab**
   - Last 30 days history
   - Expandable details
   - Status, date, URL

3. **Email Monitor Tab**
   - Manual email check
   - Display detected responses
   - Classification and confidence

4. **Setup Tab**
   - User profile form
   - Save to encrypted storage

## Data Flow Examples

### Complete Application Cycle

```
┌─────────────┐
│  HiringCafe │
│   RSS Feed  │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────┐
│  Parse Job Description          │
│  • Extract title, company, URL  │
│  • Download full description    │
└──────────┬──────────────────────┘
           │
           ↓
┌─────────────────────────────────┐
│  Store in Database              │
│  → listings table               │
└──────────┬──────────────────────┘
           │
           ↓
┌─────────────────────────────────┐
│  Filter Relevant Jobs           │
│  (Apply rate limiting)          │
└──────────┬──────────────────────┘
           │
           ↓
┌─────────────────────────────────┐
│  Resume Customization           │
│  1. Extract keywords            │
│  2. Check cache                 │
│  3. Customize with Ollama       │
│  4. Cache result                │
└──────────┬──────────────────────┘
           │
           ↓
┌─────────────────────────────────┐
│  Apply to Job                   │
│  1. Launch browser              │
│  2. Navigate to URL             │
│  3. Fill form (ATS adapter)     │
│  4. Upload resume               │
│  5. Click submit                │
└──────────┬──────────────────────┘
           │
           ├─ Success
           │  └─ Record: submitted
           │
           └─ Failure
              └─ Record: pending
                   (with error notes)
           │
           ↓
┌─────────────────────────────────┐
│  Store Application Record       │
│  → applications table           │
│  → resume_versions table        │
└──────────┬──────────────────────┘
           │
           ↓
┌─────────────────────────────────┐
│  Monitor Email Responses        │
│  (Gmail/Outlook)                │
│  • Fetch last 7 days            │
│  • Classify: rejection/interview│
│  • Update application status    │
└─────────────────────────────────┘
```

## Configuration Hierarchy

```
1. Environment Variables (.env file)
   ↓
2. Config Module (config/settings.py)
   ↓ (with defaults)
3. Hardcoded Defaults
   ↓
4. Runtime Overrides (function parameters)
```

## Async/Await Pattern

```python
async def main():
    # Parallel scraping
    scraper = HiringCafeScraper()
    jobs = await scraper.scrape()
    
    # Sequential applications (rate limiting)
    for job in jobs:
        resume, keywords = await customizer.customize_resume(...)
        success = await applier.apply_to_job(...)
        await asyncio.sleep(3)  # Polite delay
    
    # Sync email check (IMAP is sync-only in Python)
    monitor = EmailMonitor()
    emails = monitor.get_recent_emails()
```

## Error Handling Strategy

```python
try:
    # Component operation
    result = await operation()
except specific_exception as e:
    # Log with context
    logger.error(f"Operation failed: {e}", exc_info=True)
    # Continue or retry
    if should_retry(e):
        return await retry_operation()
    else:
        return default_value
except Exception as e:
    # Catch-all for unexpected errors
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return None
finally:
    # Cleanup resources
    await cleanup()
```

## Performance Considerations

1. **Resume Caching** - Avoid regenerating for similar jobs
2. **Batch Operations** - Process multiple jobs in sequence (not parallel)
3. **Rate Limiting** - 3-second delay between applications
4. **Connection Pooling** - Reuse IMAP connections
5. **Lazy Loading** - Load database only when needed

## Security Layers

1. **Environment Isolation** - .env not in git
2. **Credential Encryption** - Fernet for local storage
3. **App Passwords** - Limited scope for email
4. **No Cloud** - All processing local
5. **Audit Logs** - Full activity trail

---

**Built for scalability, reliability, and zero-dependency deployment.**
