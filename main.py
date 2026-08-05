import os
import time
import config
from database import init_db, log_job_processed
from auth import SESSION_DIR
from job_scraper import scrape_jobs
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
        
        # 1. Scrape Jobs
        jobs = scrape_jobs(page, config)
        print(f"Found {len(jobs)} new jobs to evaluate.")

        # 2. Process each job
        for job in jobs:
            if messages_sent_today >= config.MAX_MESSAGES_PER_DAY:
                print("Reached daily message limit. Stopping for today.")
                break

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
                    
        print(f"Finished run. Sent {messages_sent_today} messages.")
        context.close()

if __name__ == "__main__":
    main()
