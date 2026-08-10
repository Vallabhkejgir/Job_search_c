import re

with open('main.py', 'r') as f:
    content = f.read()

# Let's replace the limit check and increment logic
old_logic = """                # Check limit before processing
                if companies_processed >= config.MAX_COMPANIES_TO_PROCESS:
                    print(f"Reached MAX_COMPANIES_TO_PROCESS limit ({config.MAX_COMPANIES_TO_PROCESS}). Stopping.")
                    break
                    

                # Extract job details (this will return None and skip if already processed in DB)
                job = extract_job_from_card(page, card)
                if not job:
                    continue

                # Increment only when a company is actually processed for employee searches/messages
                companies_processed += 1"""

new_logic = """                # Extract job details (this will return None and skip if already processed in DB)
                job = extract_job_from_card(page, card)
                if not job:
                    continue

                company_name = job['company']
                if company_name not in processed_company_names:
                    if companies_processed >= config.MAX_COMPANIES_TO_PROCESS:
                        print(f"Reached MAX_COMPANIES_TO_PROCESS limit ({config.MAX_COMPANIES_TO_PROCESS}). Stopping.")
                        break
                    processed_company_names.add(company_name)
                    companies_processed += 1"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    content = content.replace("companies_processed = 0", "companies_processed = 0\n        processed_company_names = set()")
    with open('main.py', 'w') as f:
        f.write(content)
    print("Fixed main.py")
else:
    print("Could not find old logic in main.py")
