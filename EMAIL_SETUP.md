# Job Application Automation Bot - Email Setup Guide

## Email Provider Setup

The bot supports both **Gmail** and **Outlook** email providers. Choose one:

---

## Option 1: Gmail Setup

### Step 1: Create Gmail App Password

1. Go to https://myaccount.google.com/security
2. Enable "2-Step Verification" (if not already enabled)
3. Go back to Security settings
4. Look for "App passwords" (only appears with 2FA enabled)
5. Select:
   - App: **Mail**
   - Device: **Windows Computer** (or your OS)
6. Google will generate a 16-character password
7. Copy it (don't close the window)

### Step 2: Configure .env

```bash
cp .env.example .env
```

Edit `.env`:

```
EMAIL_PROVIDER=gmail
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
OLLAMA_MODEL=mistral
```

### Supported Gmail Accounts
- `@gmail.com`
- `@googlemail.com`

---

## Option 2: Outlook Setup

### Step 1: Create Outlook App Password

1. Go to https://account.microsoft.com/security
2. Click "Advanced security options"
3. Look for "App passwords" (only available with 2FA)
4. Select:
   - App: **Mail**
   - Device: **Windows Computer** (or your OS)
5. Microsoft will generate a 16-character password
6. Copy it

### Step 2: Configure .env

```bash
cp .env.example .env
```

Edit `.env`:

```
EMAIL_PROVIDER=outlook
OUTLOOK_EMAIL=your-email@outlook.com
OUTLOOK_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
OLLAMA_MODEL=mistral
```

### Supported Outlook Accounts
- `@outlook.com`
- `@hotmail.com`
- `@live.com`
- `@microsoft.com`

---

## Troubleshooting Email Setup

### "AUTHENTICATIONFAILED" Error

**Problem:** `[AUTHENTICATIONFAILED] Login failed`

**Solution:**
1. Make sure you're using an **App Password**, NOT your regular password
2. Verify 2FA is enabled on your account
3. Regenerate a new app password
4. Copy-paste the password exactly (no extra spaces)

### "Connection refused" Error

**Problem:** `Connection refused to outlook.office365.com:993`

**Solution:**
1. Check your internet connection
2. Verify the server name is correct (outlook.office365.com)
3. Try disabling firewall temporarily

### "IMAP is disabled" Error (Gmail)

**Problem:** `[IMAP4APPARENTLY] Response from Gmail`

**Solution:**
1. Go to https://myaccount.google.com/lesssecureapps
2. Enable "Less secure app access" (alternative to app passwords)
3. OR use an app password instead

### No Emails Retrieved

**Problem:** Bot runs but finds no emails

**Solution:**
1. Enable DEBUG logging in `.env`: `APP_LOG_LEVEL=DEBUG`
2. Check that emails are in INBOX (not other folders)
3. Verify the mailbox has recent emails from last 7 days
4. Check your email settings allow IMAP access

---

## Testing Email Connection

### Test Gmail

```python
from monitoring import EmailMonitor

monitor = EmailMonitor()
emails = monitor.get_recent_emails(days=7)
print(f"Found {len(emails)} emails")
for subject, sender, body in emails[:3]:
    print(f"From: {sender}")
    print(f"Subject: {subject}")
    print(f"Body: {body[:100]}...\n")
```

### Test Outlook

```python
import os
os.environ['EMAIL_PROVIDER'] = 'outlook'

from monitoring import EmailMonitor

monitor = EmailMonitor()
emails = monitor.get_recent_emails(days=7)
print(f"Found {len(emails)} emails")
for subject, sender, body in emails[:3]:
    print(f"From: {sender}")
    print(f"Subject: {subject}")
    print(f"Body: {body[:100]}...\n")
```

---

## Email Classification

The bot automatically classifies emails as:

### Rejection ❌
Keywords detected:
- "reject", "not selected", "unsuccessful"
- "not move forward", "decline", "position filled"

**Confidence:** 95%

### Interview 📞
Keywords detected:
- "interview", "next step", "move forward"
- "screening call", "technical round", "schedule"

**Confidence:** 90%

### Submitted ✅
Keywords detected:
- "received", "acknowledge", "applied"
- "thank you for applying", "application received"

**Confidence:** 70%

---

## Email Monitoring Features

### Automatic Email Checking
- Checks email every 6 hours (configurable in `.env`)
- Looks back 7 days for responses
- Classifies emails by type
- Logs all detected responses

### Dashboard Integration
1. Run: `streamlit run dashboard.py`
2. Go to "Email Monitor" tab
3. Click "Check Emails Now"
4. View detected responses

### Manual Email Check

```python
import asyncio
from monitoring import EmailMonitor

monitor = EmailMonitor()
emails = monitor.get_recent_emails(days=7)
statuses = monitor.parse_application_status(emails)

for status in statuses:
    print(f"From: {status['sender']}")
    print(f"Type: {status['status_type']} ({status['confidence']:.0%})")
```

---

## Security Best Practices

✅ **DO:**
- Use App Passwords (not your regular password)
- Keep `.env` file in `.gitignore`
- Enable 2FA on your email account
- Rotate app passwords periodically
- Run bot on a trusted machine

❌ **DON'T:**
- Store passwords in code
- Commit `.env` to Git
- Use regular password (use App Password)
- Share your app password
- Run bot on untrusted machines

---

## Switching Email Providers

To switch from Gmail to Outlook:

```bash
# Edit .env
EMAIL_PROVIDER=outlook
OUTLOOK_EMAIL=your-outlook@outlook.com
OUTLOOK_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# Remove old Gmail settings
# GMAIL_EMAIL=...
# GMAIL_APP_PASSWORD=...
```

Then restart the bot.

---

## Support

If you encounter email issues:

1. **Check logs:**
   ```bash
   tail -f logs/job_bot.log | grep -i email
   ```

2. **Enable debug mode:**
   ```
   APP_LOG_LEVEL=DEBUG
   ```

3. **Test IMAP directly:**
   ```python
   import imaplib
   
   # For Gmail
   mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
   mail.login("your-email@gmail.com", "your-app-password")
   
   # For Outlook
   mail = imaplib.IMAP4_SSL("outlook.office365.com", 993)
   mail.login("your-email@outlook.com", "your-app-password")
   
   print("Connection successful!")
   mail.logout()
   ```

4. **Open an issue** with your logs (redact email/password)

---

**The bot works with both Gmail and Outlook seamlessly. Pick the one you prefer!**
