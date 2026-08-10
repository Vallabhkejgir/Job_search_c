import os

from playwright.sync_api import sync_playwright

import config
from auth import SESSION_DIR
from database import get_total_jobs_in_db, init_db, log_job_processed
from job_scraper import extract_job_from_card, load_job_search_page
from messenger import search_employees, send_connection_request


def main():
    print("=" * 50)
    print("STARTING LINKEDIN REFERRAL AGENT")
    print(f"Mode: {'DRY RUN' if config.DRY_RUN else 'LIVE'}")
    print(f"Targeting: {config.SEARCH_KEYWORDS} in {config.SEARCH_LOCATION}")
    print("=" * 50)

    init_db()

    if not os.path.exists(SESSION_DIR):
        print("Session directory not found. Please run auth.py first to log in.")
        return

    messages_sent_today = 0

    with sync_playwright() as p:
        # Launch unauthenticated browser for public job search (bypasses authenticated SPA redirects)
        public_browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        public_page = public_browser.new_page()

        # Launch persistent context for authenticated employee search and sending connection requests
        auth_context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 800},
        )
        auth_page = (
            auth_context.pages[0] if auth_context.pages else auth_context.new_page()
        )

        total_jobs_found_in_run = 0
        start = 0
        companies_processed = 0
        processed_company_names = set()

        while start < 1000:
            # 1. Load Job Search Page using public page for full card listings
            num_cards, card_selector = load_job_search_page(
                public_page, config, start
            )
            if num_cards == 0:
                if start == 0:
                    print("No jobs found or unable to load job search page.")
                else:
                    print("No more jobs found.")
                break

            total_jobs_found_in_run += num_cards

            # 2. Interleaved Process: Extract -> Search Employees -> Message
            for i in range(num_cards):
                # Dynamically locate card element in public search results list
                card = public_page.locator(card_selector).nth(i)

                # Extract job details
                job = extract_job_from_card(public_page, card)
                if not job:
                    continue

                company_name = job["company"]
                if company_name not in processed_company_names:
                    if companies_processed >= config.MAX_COMPANIES_TO_PROCESS:
                        print(
                            f"Reached MAX_COMPANIES_TO_PROCESS limit ({config.MAX_COMPANIES_TO_PROCESS}). Stopping."
                        )
                        break
                    processed_company_names.add(company_name)
                    companies_processed += 1

                # Without AI evaluation, every job matching search query is processed
                match_reason = f"Relevant opening for {job['title']}"
                target_titles = [
                    "Recruiter",
                    "Engineering Manager",
                    "Hiring Manager",
                ]

                # Log job
                log_job_processed(
                    job["job_id"], job["title"], job["company"], True, match_reason
                )

                print(f"Processing job match: {job['title']} at {job['company']}")

                # Check daily message limit
                if messages_sent_today >= config.MAX_MESSAGES_PER_DAY:
                    print(
                        f"Daily message limit ({config.MAX_MESSAGES_PER_DAY}) reached. Skipping messaging."
                    )
                    continue

                # 3. Find employees using the authenticated session
                try:
                    employees = search_employees(
                        auth_page,
                        job.get("company_url"),
                        job["company"],
                        target_titles,
                    )

                    # 4. Message employees using authenticated session
                    messaged_for_this_company = 0
                    for emp in employees:
                        if messages_sent_today >= config.MAX_MESSAGES_PER_DAY:
                            break
                        if messaged_for_this_company >= config.MAX_PEOPLE_PER_COMPANY:
                            break

                        success = send_connection_request(
                            auth_page, emp, job, match_reason, config
                        )

                        if success:
                            messages_sent_today += 1
                            messaged_for_this_company += 1
                except Exception as e:  # noqa: BLE001
                    print(f"Error processing outreach for {job['company']}: {e}")

            if companies_processed >= config.MAX_COMPANIES_TO_PROCESS:
                break

            # Move to the next page
            start += num_cards

        total_jobs_in_db = get_total_jobs_in_db()
        print(
            f"Finished run. Jobs found in run: {total_jobs_found_in_run}. Total jobs in DB: {total_jobs_in_db}. Sent {messages_sent_today} messages."
        )
        public_browser.close()
        auth_context.close()


if __name__ == "__main__":
    main()
