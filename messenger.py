import random

from database import is_user_messaged, log_user_messaged


def search_employees(page, company_url, company_name, target_titles):
    """
    Search for employees at a specific company with target titles by visiting the company's People tab.
    """
    print(f"Searching for employees at {company_name}...")
    employees = []

    if not company_url:
        print(
            f"No company URL found for {company_name}. Cannot search their People tab."
        )
        return employees

    # Ensure the company URL ends with a slash before appending "people/"
    if not company_url.endswith("/"):
        company_url += "/"

    people_url = f"{company_url}people/"
    print(f"Navigating to company people page: {people_url}")

    try:
        page.goto(people_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(random.randint(3000, 5000))
    except Exception as e:  # noqa: BLE001
        print(f"Failed to load company people page: {e}")
        return employees

    # Type the target titles into the "Search employees" input box
    try:
        keywords = " OR ".join([f'"{title}"' for title in target_titles])
        search_input = page.locator(
            "input[placeholder*='Search employees'], input#people-search-keywords, input[aria-label*='Search employees']"
        ).first
        if search_input.count() > 0:
            search_input.fill(keywords)
            search_input.press("Enter")
            page.wait_for_timeout(random.randint(4000, 6000))
        else:
            print(
                "Could not find the search box on the company People tab. Proceeding with raw list."
            )
    except Exception as e:  # noqa: BLE001
        print(f"Error interacting with company search box: {e}")

    # Scroll slightly more aggressively to load all images/lazy loaded DOM elements
    for _ in range(3):
        page.evaluate("window.scrollBy(0, 1000)")
        page.wait_for_timeout(1000)

    # Extract profiles from the company people grid
    # Usually the grid cards contain links to profiles
    profile_links = page.locator("a[href*='/in/']").all()
    print(f"Found {len(profile_links)} profile links to evaluate on company page.")

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

            # Clean up newlines or extra text (like "is open to work" badges)
            name = name_text.split("\n")[0].strip() if name_text else ""
            if "open to work" in name.lower():
                import re

                name = re.sub(r"(?i)\s*(is\s+)?open\s+to\s+work.*", "", name).strip()

            # If inner_text was empty (e.g. image link), try extracting title or alt attribute
            if not name:
                img = link_locator.locator("img").first
                if img.count() > 0:
                    alt = img.get_attribute("alt") or ""
                    if alt and "picture" not in alt.lower():
                        name = alt.strip()

            if not name:
                continue

            # Don't add if it's not a real profile link or already messaged
            if (
                name != "LinkedIn Member"
                and "View" not in name
                and not is_user_messaged(profile_url)
            ):
                # On the company page, we don't strictly need to check if they still work there
                # because the "People" tab is specifically for current employees.
                # However, it doesn't hurt to keep a sanity check if the DOM supports it.
                parent_container = link_locator.locator("xpath=ancestor::li").first
                if parent_container.count() == 0:
                    # In company people grids, the container is often a div
                    parent_container = link_locator.locator(
                        "xpath=ancestor::div[contains(@class, 'org-people-profile-card') or contains(@class, 'entity-result__item')]"
                    ).first

                if parent_container.count() > 0:
                    container_text = parent_container.inner_text()
                    lines = [
                        line.strip()
                        for line in container_text.split("\n")
                        if line.strip()
                    ]
                    if len(lines) > 0 and lines[0]:
                        name = lines[0]

            # Clean up open to work or other extra text from name
            if "open to work" in name.lower():
                import re

                name = re.sub(r"(?i)\s*(is\s+)?open\s+to\s+work.*", "", name).strip()

            employees.append(
                {"name": name, "profile_url": profile_url, "company": company_name}
            )

            if len(employees) >= 10:  # Collect up to 10 valid candidates
                break

        except Exception as e:  # noqa: BLE001
            print(f"Error extracting profile: {e}")

    print(f"Found {len(employees)} potential contacts at {company_name}.")
    return employees


def send_connection_request(page, employee, job, ai_pitch, config):
    """
    Navigates to profile and sends connection request with a note.
    """
    print(f"Preparing to message {employee['name']} ({employee['profile_url']})")

    # Extract first name
    first_name = (
        employee["name"].split(" ")[0] if " " in employee["name"] else employee["name"]
    )

    message = f"Hi {first_name},\n\nI noticed the {job['title']} opening at {job['company']}. I'd be a great fit because {ai_pitch}\n\nWould you be open to a quick chat or referring me?\n\nThanks!"

    if len(message) > 300:
        # LinkedIn connection note limit is 300 chars
        print(f"Message too long ({len(message)} chars). Truncating...")
        message = message[:297] + "..."

    print(f"Draft Message:\n---\n{message}\n---")

    if config.DRY_RUN:
        print(f"DRY RUN: Skipping actual send to {employee['name']}")
        # Log it anyway for testing flow
        log_user_messaged(
            employee["profile_url"],
            employee["name"],
            employee["company"],
            job["job_id"],
        )
        return True

    try:
        # Actually navigate and send
        page.goto(employee["profile_url"])
        page.wait_for_timeout(random.randint(3000, 5000))

        # Click connect
        connect_btn = page.locator("button[aria-label^='Invite']").first
        if connect_btn.count() == 0:
            # Sometimes it's under 'More'
            more_btn = page.locator("button[aria-label='More actions']").first
            if more_btn.count() > 0:
                more_btn.click()
                page.wait_for_timeout(1000)
                connect_btn = page.locator(
                    "div.artdeco-dropdown__content button[aria-label^='Invite']"
                ).first

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
            log_user_messaged(
                employee["profile_url"],
                employee["name"],
                employee["company"],
                job["job_id"],
            )

            # Sleep to avoid rate limits
            sleep_time = random.randint(15000, 30000)
            print(f"Sleeping for {sleep_time/1000}s to avoid rate limits...")
            page.wait_for_timeout(sleep_time)
            return True
        else:
            print("Could not find 'Add a note' button.")
            return False

    except Exception as e:  # noqa: BLE001
        print(f"Error sending message to {employee['name']}: {e}")
        return False
