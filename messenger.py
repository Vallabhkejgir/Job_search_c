import random
import re

from database import is_user_messaged, log_user_messaged


def search_employees(page, company_url, company_name, target_titles):
    """
    Search for employees at a specific company with target titles by visiting the company's People tab.
    Sanitizes extracted employee names (removing badges like 'is open to work', normalizing multiple spaces) and ensures returned profile URLs are absolute.
    """
    print(f"[Search] Searching for contacts at {company_name}...")
    employees = []

    if not company_url:
        return employees

    # Ensure the company URL ends with a slash before appending "people/"
    if not company_url.endswith("/"):
        company_url += "/"

    people_url = f"{company_url}people/"

    try:
        page.goto(people_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(random.randint(3000, 5000))
    except Exception as e:  # noqa: BLE001
        print(f"Failed to load company people page for {company_name}: {e}")
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
    except Exception:  # noqa: BLE001, S110
        pass

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

            profile_url = profile_url.rstrip("/")

            if profile_url.startswith("http://"):
                profile_url = "https://" + profile_url[7:]

            if profile_url.startswith("/"):
                profile_url = f"https://www.linkedin.com{profile_url}"
            elif not profile_url.startswith("http"):
                profile_url = f"https://www.linkedin.com/{profile_url}"

            if profile_url in seen_urls:
                continue

            # Since the layout changed, grab the name from the text inside the link
            # The name is usually the bolded text or the only text
            name_text = link_locator.inner_text().strip()

            # Clean up newlines or extra text (like "is open to work" badges)
            # Sometimes a name might be split by multiple spaces or newlines
            name = name_text.split("\n")[0].strip() if name_text else ""
            name = " ".join(name.split())

            # Extract name if it starts with View ...
            if name.lower().startswith("view "):
                name = re.sub(r"(?i)^view\s+", "", name)

            # If inner_text was empty (e.g. image link), try extracting title or alt attribute
            if not name:
                img = link_locator.locator("img").first
                if img.count() > 0:
                    alt = img.get_attribute("alt") or ""
                    if alt and "picture" not in alt.lower():
                        name = alt.strip()
                        if name.lower().startswith("view "):
                            name = re.sub(r"(?i)^view\s+", "", name)

            if not name:
                continue

            # Clean up open to work or other extra text from name
            name = re.sub(r"(?i)\s*(is\s+)?open\s+to\s+work.*", "", name)
            name = re.sub(r"(?i)\s*follows this page.*", "", name)
            name = re.sub(r"(?i)\s*works here.*", "", name)
            name = re.sub(r"(?i)\s*View .*'s profile.*", "", name)
            # Remove any trailing "’s profile" or similar
            name = re.sub(
                r"(?i)(?:[’\'\`]s?|\bs)?\s*\b(profile|graphic link|picture|photo|link)\b.*",
                "",
                name,
            )
            name = name.strip()

            invalid_terms = {
                "post",
                "linkedin member",
                "follow",
                "connect",
                "view",
                "like",
                "comment",
                "member",
                "graphic link",
                "picture",
            }

            if (
                name.lower() in invalid_terms
                or name.lower() == company_name.lower()
                or len(name) < 2
                or is_user_messaged(profile_url)
            ):
                continue

            seen_urls.add(profile_url)

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
    Extracts and sanitizes the first name by handling titles, possessives, and trailing symbols to avoid empty or broken messages.
    """
    print(f"[Target] Contact: {employee['name']} ({employee['profile_url']})")

    # Extract first name
    # Clean up prefixes like Dr. or Mr. to get the actual first name
    raw_name = employee["name"]
    # Handle multiple spaces correctly to avoid empty strings
    name_parts = [p for p in raw_name.split() if p.strip()]

    # If the first word is a title, take the second word
    if len(name_parts) > 1 and name_parts[0].lower().replace(".", "") in [
        "mr",
        "ms",
        "mrs",
        "dr",
        "prof",
        "er",
    ]:
        first_name = name_parts[1]
    elif len(name_parts) > 0:
        first_name = name_parts[0]
    else:
        first_name = raw_name

    # Strip any trailing symbols or non-alpha characters from first name just to be safe
    # Also correctly handle trailing possessives without breaking non-ASCII characters
    first_name = re.sub(r"[\W\d_]+$", "", first_name)
    first_name = re.sub(r"(?i)[’\'\`]s?$", "", first_name)

    # Hard-fail check: If somehow we ended up with an empty first name, fallback to full raw name or generic
    if not first_name.strip():
        first_name = raw_name.strip() or "there"

    user_intro = getattr(config, "USER_INTRODUCTION", "").strip()
    if user_intro:
        message = f"Hi {first_name},\n\nI noticed the {job['title']} opening at {job['company']}.\n\n{user_intro}\n\nWould you be open to a quick chat or referring me?\n\nThanks!"
    else:
        message = f"Hi {first_name},\n\nI noticed the {job['title']} opening at {job['company']}. I'd be a great fit because {ai_pitch}\n\nWould you be open to a quick chat or referring me?\n\nThanks!"

    if len(message) > 300:
        # LinkedIn connection note limit is 300 chars
        message = message[:297] + "..."

    print(f"Draft Message:\n---\n{message}\n---")

    if config.DRY_RUN:
        print(f"[DRY RUN] Skipping send to {employee['name']}\n")
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
        connect_btn = page.locator(
            "main button:has-text('Connect'), main a:has-text('Connect'), button[aria-label*='Connect'], button[aria-label*='Invite']"
        ).first
        if connect_btn.count() == 0 or not connect_btn.is_visible():
            # Sometimes it's under 'More'
            more_btn = page.locator(
                "main button[aria-label='More actions'], main button[aria-label='More']"
            ).first
            if more_btn.count() > 0:
                more_btn.click(force=True)
                page.wait_for_timeout(1000)
                connect_btn = page.locator(
                    "div[role='menu'] *:has-text('Connect'), div.artdeco-dropdown__content *:has-text('Connect'), ul *:has-text('Connect')"
                ).first

        if connect_btn.count() == 0:
            print(f"Could not find Connect button for {employee['name']}")
            return False

        connect_btn.click(force=True)
        page.wait_for_timeout(random.randint(1500, 2500))

        # Add note
        add_note_btn = page.locator(
            "button:has-text('Add a note'), button[aria-label='Add a note'], button:has-text('Add note')"
        ).first
        if add_note_btn.count() > 0:
            add_note_btn.click(force=True)
            page.wait_for_timeout(1000)

            # Type message
            page.locator(
                "textarea[name='message'], textarea#custom-message, textarea"
            ).first.fill(message)
            page.wait_for_timeout(random.randint(1000, 2000))

            # Click send
            send_btn = page.locator(
                "button:has-text('Send'), button[aria-label='Send invitation'], button[aria-label='Send now']"
            ).first
            send_btn.click(force=True)

            print(f"Successfully sent connection request to {employee['name']}")
            log_user_messaged(
                employee["profile_url"],
                employee["name"],
                employee["company"],
                job["job_id"],
            )

            # Sleep to avoid rate limits
            sleep_time = random.randint(15000, 30000)
            print(f"Sleeping for {sleep_time / 1000}s to avoid rate limits...")
            page.wait_for_timeout(sleep_time)
            return True
        else:
            print("Could not find 'Add a note' button.")
            return False

    except Exception as e:  # noqa: BLE001
        print(f"Error sending message to {employee['name']}: {e}")
        return False
