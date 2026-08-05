import os
import time
import config
from database import init_db, log_job_processed
from auth import SESSION_DIR
from job_scraper import load_job_search_page, extract_job_from_card
from ai_evaluator import evaluate_job
from messenger import search_employees, send_connection_request
from playwright.sync_api import sync_playwright

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
        # Launch browser with saved session
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False, # Often safer to run headful to avoid bot detection
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 800}
        )
        
        page = context.pages[0] if context.pages else context.new_page()

        # 1. Load Job Search Page
        num_cards = load_job_search_page(page, config)
        if num_cards == 0:
            print("No jobs found or unable to load job search page.")
            return

        TARGET_EVALUATIONS = 15
        jobs_evaluated_today = 0

        # 2. Interleaved Process: Extract -> Evaluate -> Search Employees -> Message
        for i in range(num_cards):
            if messages_sent_today >= config.MAX_MESSAGES_PER_DAY:
                print("Reached daily message limit. Stopping for today.")
                break

            if jobs_evaluated_today >= TARGET_EVALUATIONS:
                print(f"Reached target of {TARGET_EVALUATIONS} new evaluations. Stopping.")
                break

            # Dynamically locate the card to avoid stale element references if the DOM shifted
            card = page.locator(".job-card-container").nth(i)

            # Extract job details (this will return None and skip if already processed in DB)
            job = extract_job_from_card(page, card)
            if not job:
                continue

            jobs_evaluated_today += 1

            # Evaluate with AI
            evaluation = evaluate_job(job, config)

            # Log job
            log_job_processed(
                job['job_id'],
                job['title'],
                job['company'],
                evaluation.is_match,
                evaluation.match_reason
            )

            if not evaluation.is_match:
                print(f"AI determined {job['company']} is NOT a match. Skipping.")
                continue

            print(f"AI MATCH! Reason: {evaluation.match_reason}")

            # 3. Find employees using a dedicated worker tab
            worker_page = context.new_page()
            try:
                employees = search_employees(worker_page, job.get('company_url'), job['company'], evaluation.target_titles)

                # 4. Message employees
                messaged_for_this_company = 0
                for emp in employees:
                    if messages_sent_today >= config.MAX_MESSAGES_PER_DAY:
                        break
                    if messaged_for_this_company >= config.MAX_PEOPLE_PER_COMPANY:
                        break

                    success = send_connection_request(worker_page, emp, job, evaluation.match_reason, config)

                    if success:
                        messages_sent_today += 1
                        messaged_for_this_company += 1
            finally:
                worker_page.close()

            # Return to the main tab context visually (optional, Playwright handles it internally)
            page.bring_to_front()
            page.wait_for_timeout(1000)

        print(f"Finished run. Sent {messages_sent_today} messages.")
        context.close()

if __name__ == "__main__":
    main()
