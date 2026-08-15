with open("main.py", "r") as f:
    content = f.read()

old_str = """                    # Check daily message limit
                    if messages_sent_today >= config.MAX_MESSAGES_PER_DAY:
                        print(f"Daily message limit ({config.MAX_MESSAGES_PER_DAY}) reached. Skipping messaging.")
                        break

                    # Launch authenticated context per job"""

new_str = """                    # Check daily message limit
                    if messages_sent_today >= config.MAX_MESSAGES_PER_DAY:
                        print(f"Daily message limit ({config.MAX_MESSAGES_PER_DAY}) reached. Skipping messaging.")
                        break

                    messaged_for_this_company = company_message_counts.get(company_name, 0)
                    if messaged_for_this_company >= config.MAX_PEOPLE_PER_COMPANY:
                        print(f"Company limit ({config.MAX_PEOPLE_PER_COMPANY}) reached for {company_name}. Skipping outreach.")
                        continue

                    # Launch authenticated context per job"""

content = content.replace(old_str, new_str)
with open("main.py", "w") as f:
    f.write(content)
