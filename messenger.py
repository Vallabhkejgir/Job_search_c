import urllib.parse
import time
import random
from database import is_user_messaged, log_user_messaged

def search_employees(page, company_name, target_titles):
    """
    Search for employees at a specific company with target titles.
    """
    print(f"Searching for employees at {company_name}...")
    employees = []
    
    # We construct a people search URL directly
    # Keywords are target titles OR'd together
    keywords = " OR ".join([f'"{title}"' for title in target_titles])
    
    # Simple search for the company and title keywords in people
    search_query = f"{company_name} {keywords}"
    encoded_query = urllib.parse.urlencode({"keywords": search_query})
    search_url = f"https://www.linkedin.com/search/results/people/?{encoded_query}"
    
    page.goto(search_url)
    page.wait_for_timeout(random.randint(3000, 5000))
    
    # Wait for results
    try:
        # Check standard container or fallbacks
        try:
            page.wait_for_selector(".reusable-search__result-container", timeout=10000)
        except:
            try:
                page.wait_for_selector(".search-results-container", timeout=10000)
            except:
                page.wait_for_selector("a[href*='/in/']", timeout=10000)
    except:
        print(f"No employee results found for {company_name}")
        return employees

    # Scroll slightly
    page.evaluate("window.scrollBy(0, 500)")
    page.wait_for_timeout(1000)

    # Extract profiles. We use a broad locator that gets people links
    # Then we walk up to the container, or just process the links directly
    profile_links = page.locator("a[href*='/in/']").all()

    # Use a set to deduplicate since links often appear twice (image and text)
    seen_urls = set()

    for link_locator in profile_links:
        try:
            profile_url = link_locator.get_attribute("href")
            if not profile_url:
                continue

            # Clean URL
            if "?" in profile_url:
                profile_url = profile_url.split("?")[0]

            if profile_url in seen_urls:
                continue

            seen_urls.add(profile_url)

            # Since the layout changed, grab the name from the text inside the link
            # The name is usually the bolded text or the only text
            name_text = link_locator.inner_text().strip()

            # Clean up newlines or extra text (like "View profile")
            name = name_text.split('\n')[0].strip() if name_text else "Unknown"

            # Don't add if it's not a real profile link or already messaged
            if name and name != "LinkedIn Member" and "View" not in name and not is_user_messaged(profile_url):
                # Verify they actually work at the company by checking the parent container text
                parent_container = link_locator.locator("xpath=ancestor::li").first
                if parent_container.count() == 0:
                    parent_container = link_locator.locator("xpath=ancestor::div[contains(@class, 'search-results-container') or contains(@class, 'entity-result__item')]").first

                if parent_container.count() > 0:
                    full_text = parent_container.inner_text().lower()
                    if company_name.lower() not in full_text:
                        print(f"Skipping {name} - '{company_name}' not found in their headline.")
                        continue

                employees.append({
                    "name": name,
                    "profile_url": profile_url,
                    "company": company_name
                })

                if len(employees) >= 5:  # Top 5 max
                    break

        except Exception as e:
            print(f"Error extracting profile: {e}")

    print(f"Found {len(employees)} potential contacts at {company_name}.")
    return employees

def send_connection_request(page, employee, job, ai_pitch, config):
    """
    Navigates to profile and sends connection request with a note.
    """
    print(f"Preparing to message {employee['name']} ({employee['profile_url']})")
    
    # Extract first name
    first_name = employee['name'].split(" ")[0] if " " in employee['name'] else employee['name']
    
    message = f"Hi {first_name},\n\nI noticed the {job['title']} opening at {job['company']}. I'd be a great fit because {ai_pitch}\n\nWould you be open to a quick chat or referring me?\n\nThanks!"
    
    if len(message) > 300:
        # LinkedIn connection note limit is 300 chars
        print(f"Message too long ({len(message)} chars). Truncating...")
        message = message[:297] + "..."
        
    print(f"Draft Message:\n---\n{message}\n---")
    
    if config.DRY_RUN:
        print(f"DRY RUN: Skipping actual send to {employee['name']}")
        # Log it anyway for testing flow
        log_user_messaged(employee['profile_url'], employee['name'], employee['company'], job['job_id'])
        return True
        
    try:
        # Actually navigate and send
        page.goto(employee['profile_url'])
        page.wait_for_timeout(random.randint(3000, 5000))
        
        # Click connect
        connect_btn = page.locator("button[aria-label^='Invite']").first
        if connect_btn.count() == 0:
            # Sometimes it's under 'More'
            more_btn = page.locator("button[aria-label='More actions']").first
            if more_btn.count() > 0:
                more_btn.click()
                page.wait_for_timeout(1000)
                connect_btn = page.locator("div.artdeco-dropdown__content button[aria-label^='Invite']").first
                
        if connect_btn.count() == 0:
            print(f"Could not find Connect button for {employee['name']}")
            return False
            
        connect_btn.click()
        page.wait_for_timeout(random.randint(1000, 2000))
        
        # Add note
        add_note_btn = page.locator("button[aria-label='Add a note']")
        if add_note_btn.count() > 0:
            add_note_btn.click()
            page.wait_for_timeout(1000)
            
            # Type message
            page.locator("textarea[name='message']").fill(message)
            page.wait_for_timeout(random.randint(1000, 2000))
            
            # Click send
            send_btn = page.locator("button[aria-label='Send invitation']")
            send_btn.click()
            
            print(f"Successfully sent connection request to {employee['name']}")
            log_user_messaged(employee['profile_url'], employee['name'], employee['company'], job['job_id'])
            
            # Sleep to avoid rate limits
            sleep_time = random.randint(15000, 30000)
            print(f"Sleeping for {sleep_time/1000}s to avoid rate limits...")
            page.wait_for_timeout(sleep_time)
            return True
        else:
            print("Could not find 'Add a note' button.")
            return False
            
    except Exception as e:
        print(f"Error sending message to {employee['name']}: {e}")
        return False
