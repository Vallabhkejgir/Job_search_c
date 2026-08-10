# LinkedIn Job Referral Agent

An automated agent that searches for recent job postings on LinkedIn and automatically messages relevant company employees to request a referral.

## Features
- **Stealthy Browser Automation:** Uses Playwright with a persistent session to navigate LinkedIn securely.
- **Automated Outreach:** Automatically drafts a connection request and sends it to recruiters or engineering managers at the hiring company.
- **Idempotent & Safe:** Uses SQLite to track processed jobs and messaged users so it never spams or duplicates effort. Respects strict rate limits.

## Setup

1. **Install Dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Configure Environment**
   Copy `.env.example` to `.env` and fill in your details:
   ```bash
   cp .env.example .env
   ```
   Key environment variables:
   - `DRY_RUN`: Set to `True` for dry run testing (drafts messages without sending).
   - `SEARCH_KEYWORDS`: Job search query (e.g., `"AI Engineer"`).
   - `SEARCH_LOCATION`: Location for job search (e.g., `"India"`).
   - `MAX_COMPANIES_TO_PROCESS`: Maximum number of distinct companies to process per run (default: 10).
   - `MAX_PEOPLE_PER_COMPANY`: Maximum number of people to message per company (default: 3).
   - `USER_INTRODUCTION`: Custom introduction sentence used directly in connection request notes.

3. **Login & Save Session**
   ```bash
   python auth.py
   ```
   A browser will open. Log into LinkedIn manually. Once you see your feed, return to the terminal and press Enter to save your session.

4. **Run the Agent**
   ```bash
   python main.py
   ```
