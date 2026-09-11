# JobApply AI CLI

Automate personalized job application emails: AI (Gemini) analyzes job descriptions,
matches them against your CV, and drafts emails; you review/approve, then it sends
via **Gmail API + OAuth 2.0**.

## Requirements

- Python 3.10+
- A Gemini API key
- Gmail OAuth 2.0 credentials (Desktop App) — only if you want to actually send email

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt
pip install -e .

# 2. Configure
cp .env.example .env        # edit .env: set AI_API_KEY (and Gmail vars if sending)

# 3. Initialize + import your CV (once)
jobapply init
jobapply profile import "data/cv/CV.pdf"
```

Then either run the interactive menu (recommended) or individual commands:

```bash
jobapply            # interactive menu — loops until you Exit
```

Or step-by-step:

```bash
jobapply auth gmail     # one-time Gmail OAuth login (opens browser)
jobapply job add        # add job applications (or `job import data/jobs.csv`)
jobapply analyze        # analyze job descriptions
jobapply generate       # draft emails
jobapply review list    # review / approve / edit / regenerate
jobapply schedule set   # send now / 08:00 / custom
jobapply history list   # view sent history
```

## `.env` essentials

```env
AI_API_KEY=your_gemini_api_key

# Gmail (optional, only to send)
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_SENDER_EMAIL=you@gmail.com

EMAIL_DRY_RUN=true      # keep true while testing (emails not actually sent)
DEFAULT_PORTFOLIO_PATH= # optional portfolio PDF attached alongside CV
```

## Gmail OAuth setup (one-time)

1. In [Google Cloud Console](https://console.cloud.google.com/): create a project, enable the **Gmail API**.
2. Configure the OAuth consent screen (add your Gmail as a test user).
3. Create an OAuth Client of type **Desktop App**.
4. Put the **Client ID / Secret** into `.env` (`GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`).
5. Run `jobapply auth gmail` → approve in the browser.

No Gmail password or App Password is needed — login happens in the browser, and the
refresh token is stored locally in `data/auth/gmail_token.json` (never committed).

## Safety

- Emails are never sent without your approval (confirmations default to **No**).
- `MAX_EMAILS_PER_BATCH` and duplicate detection guard against mass sends.
- AI is restricted to verified CV facts; OAuth secrets/tokens are never printed, logged, or sent to the AI.

## Tests

```bash
python -m pytest tests/ -q
```
#