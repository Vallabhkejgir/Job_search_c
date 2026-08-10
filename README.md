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
   Edit the `.env` file or `config.py` with your search preferences.
   - Set `DRY_RUN=True` for testing.
   - Set `MAX_COMPANIES_TO_PROCESS` to limit the number of companies processed per run (default: 10).

3. **Login & Save Session**
   ```bash
   python auth.py
   ```
   A browser will open. Log into LinkedIn manually. Once you see your feed, return to the terminal and press Enter to save your session.

4. **Run the Agent**
   ```bash
   python main.py
   ```
