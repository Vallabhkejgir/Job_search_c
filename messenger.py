import random
import re

from database import is_user_messaged, log_user_messaged


def search_employees(page, company_url, company_name, target_titles):
    """
    Search for employees at a specific company with target titles by visiting the company's People tab.
    Sanitizes extracted employee names (removing badges like 'is open to work', normalizing multiple spaces, and stripping 'View' prefixes to prevent 'Hi View' greetings) and ensures returned profile URLs are absolute.
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
            # Remove any trailing "’s profile" or similar
            name = re.sub(
                r"(?i)(?:[’\'\`]s?|\bs)?\s*\b(profile|graphic link|picture|photo|link)\b.*",
                "",
                name,
            )

            # Additional fallback to remove isolated "view" or similar from the name if it still sneaks in
            name = re.sub(r"(?i)^view\b\s*", "", name)

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
    Extracts and sanitizes the first name by handling titles, possessives, and trailing symbols, safely falling back to 'there' if the name resolves exclusively to 'View' or is empty, to avoid broken messages.
    Validates that the employee's company matches the job opening company before drafting or sending outreach.
    """
    emp_company = (employee.get("company") or "").strip()
    job_company = (job.get("company") or "").strip()

    if not emp_company or not job_company:
        print(
            f"[Validation] Missing company info (Employee: '{emp_company}', Job: '{job_company}'). Skipping message."
        )
        return False

    emp_norm = re.sub(r"[^\w\s]", "", emp_company).strip().lower()
    job_norm = re.sub(r"[^\w\s]", "", job_company).strip().lower()

    if emp_norm != job_norm and emp_norm not in job_norm and job_norm not in emp_norm:
        print(
            f"[Validation] Company mismatch: Employee company '{emp_company}' does not match Job company '{job_company}'. Skipping message."
        )
        return False

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
    first_name = re.sub(r"(?i)[’\'\`]s?(?=[\W\d_]*$)", "", first_name)
    first_name = re.sub(r"[\W\d_]+$", "", first_name)

    # Hard-fail check: If somehow we ended up with an empty first name, fallback to full raw name or generic
    if not first_name.strip() or first_name.lower() == "view":
        first_name = raw_name.strip()
        # Fallback to avoid sending "Hi View" if raw name is still "view"
        if first_name.lower().startswith("view "):
            first_name = re.sub(r"(?i)^view\s+", "", first_name)

        first_name = first_name.split()[0] if first_name else "there"
        first_name = re.sub(r"(?i)[’\'\`]s?(?=[\W\d_]*$)", "", first_name)
        first_name = re.sub(r"[\W\d_]+$", "", first_name)

        if first_name.lower() == "view" or not first_name.strip():
            first_name = "there"

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

        # Validate that the employee's current company or headline matches the target job company
        try:
            profile_text = ""
            intro_card = page.locator("main section").first
            if intro_card.count() > 0:
                profile_text = intro_card.inner_text().lower()
            else:
                main_locator = page.locator("main").first
                if main_locator.count() > 0:
                    profile_text = main_locator.inner_text().lower()

            if profile_text:
                job_norm = re.sub(r"[^\w\s]", "", job_company).strip().lower()
                profile_norm = re.sub(r"[^\w\s]", "", profile_text).strip()

                if (
                    job_norm not in profile_norm
                    and job_company.lower() not in profile_text
                ):
                    print(
                        f"[Validation] Company mismatch: Profile page does not mention Job company '{job_company}'. Skipping message."
                    )
                    return False
        except Exception as e:
            print(
                f"[Validation] Warning: Could not extract profile text for validation: {e}"
            )

        # Close any open message overlay bubbles that might obscure the buttons
        try:
            close_buttons = page.locator(
                "button.msg-overlay-bubble-header__control--close-btn:visible"
            ).all()
            for btn in close_buttons:
                btn.evaluate("node => node.click()")
            page.wait_for_timeout(1000)
        except Exception:
            pass

        # Click connect
        # Need to handle different variants of the Connect button
        connect_selectors = [
            "button.pvs-profile-actions__action:has-text('Connect'):not([disabled]):visible",
            "button[aria-label*='Invite']:not([disabled]):visible",
            "button[aria-label*='Connect']:not([disabled]):visible",
            "main button:has-text('Connect'):not([disabled]):visible",
            "main a:has-text('Connect'):not([disabled]):visible",
            "button:has-text('Connect'):not([disabled]):visible",
        ]
        connect_btn = page.locator(", ".join(connect_selectors)).first

        if connect_btn.count() == 0 or not connect_btn.is_visible():
            # Sometimes it's under 'More'
            more_selectors = [
                "button.pvs-profile-actions__action:has-text('More'):visible",
                "button[aria-label='More actions']:visible",
                "button[aria-label='More']:visible",
                "main button:has-text('More'):visible",
            ]
            more_btn = page.locator(", ".join(more_selectors)).first
            if more_btn.count() > 0 and more_btn.is_visible():
                more_btn.click(force=True)
                page.wait_for_timeout(1500)

                # After clicking More, look for Connect in the dropdown
                dropdown_connect = [
                    "div.artdeco-dropdown__content button:has-text('Connect'):visible",
                    "div.artdeco-dropdown__content span:has-text('Connect'):visible",
                    "ul *:has-text('Connect'):visible",
                    "div[role='menu'] *:has-text('Connect'):visible",
                ]
                connect_btn = page.locator(", ".join(dropdown_connect)).first

        if connect_btn.count() == 0 or not connect_btn.is_visible():
            print(f"Could not find Connect button for {employee['name']}")
            return False

        # Use click(force=True) to avoid interception but wrap in try-except
        try:
            try:
                connect_btn.evaluate("node => node.click()")
            except Exception as e:
                print(f"Evaluate Connect error: {e}")
                connect_btn.click(force=True, timeout=5000)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to click Connect button: {e}")
            return False

        page.wait_for_timeout(random.randint(1500, 2500))

        # Handle 'Other' connection reason if LinkedIn asks how we know the person
        other_reason_btn = page.locator(
            "button[aria-label*='Other']:not([disabled]):visible, button:has-text('Other'):not([disabled]):visible"
        ).first
        if other_reason_btn.count() > 0 and other_reason_btn.is_visible():
            try:
                try:
                    other_reason_btn.evaluate("node => node.click()")
                except Exception as e:
                    print(f"Evaluate Other reason error: {e}")
                    other_reason_btn.click(force=True, timeout=3000)
                page.wait_for_timeout(1000)
                # Click Connect again on the modal
                modal_connect = page.locator(
                    "button[aria-label='Connect']:visible, div[role='dialog'] button.artdeco-button--primary:visible"
                ).first
                if modal_connect.count() > 0 and modal_connect.is_visible():
                    try:
                        modal_connect.evaluate("node => node.click()")
                    except Exception as e:
                        print(f"Evaluate modal Connect error: {e}")
                        modal_connect.click(force=True, timeout=3000)
                    page.wait_for_timeout(1500)
            except Exception as e:  # noqa: BLE001
                print(f"Failed to click other reason or modal connect: {e}")

        # Add note
        # If there are open messaging overlays, we should probably try to close them or ignore them, but for now we focus on the modal
        add_note_selectors = [
            "div[role='dialog'] button[aria-label='Add a note']:not([disabled]):visible",
            "div[role='dialog'] button:has-text('Add a note'):not([disabled]):visible",
            "div[role='dialog'] button:has-text('Add note'):not([disabled]):visible",
            "button[aria-label='Add a note']:not([disabled]):visible",
            "button:has-text('Add a note'):not([disabled]):visible",
            "button:has-text('Add note'):not([disabled]):visible",
            "button.artdeco-button--secondary:has-text('Add a note'):not([disabled]):visible",
        ]
        add_note_btn = page.locator(", ".join(add_note_selectors)).first

        if add_note_btn.count() > 0 and add_note_btn.is_visible():
            try:
                try:
                    add_note_btn.evaluate("node => node.click()")
                except Exception as e:
                    print(f"Evaluate Add note error: {e}")
                    add_note_btn.click(force=True, timeout=5000)
                page.wait_for_timeout(1000)

                # Type message
                msg_box = page.locator(
                    "textarea[name='message']:visible, textarea#custom-message:visible, div[role='dialog'] textarea:visible"
                ).first
                msg_box.fill(message, timeout=5000)
                page.wait_for_timeout(random.randint(1000, 2000))

                # Click send
                send_selectors = [
                    "button[aria-label='Send invitation']:visible",
                    "button[aria-label='Send now']:visible",
                    "button:has-text('Send'):visible",
                    "button:has-text('Send without a note'):visible",  # Sometimes the button text changes
                ]
                send_btn = (
                    page.locator(", ".join(send_selectors))
                    .filter(has_text=re.compile(r"Send|Send now", re.IGNORECASE))
                    .first
                )
                if send_btn.count() == 0:
                    send_btn = page.locator(", ".join(send_selectors)).first

                try:
                    send_btn.evaluate("node => node.click()")
                except Exception as e:
                    print(f"Evaluate Send error: {e}")
                    send_btn.click(force=True, timeout=5000)

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
            except Exception as e:  # noqa: BLE001
                print(f"Error while interacting with connection modal: {e}")
                return False
        else:
            print(
                "Could not find 'Add a note' button. Checking if it's already a direct message modal..."
            )
            # Debug: what modal is currently open?
            modal = page.locator("div[role='dialog']:visible").first
            if modal.count() > 0 and modal.is_visible():
                print(f"DEBUG: Visible modal text: {modal.inner_text()[:300]}")
            else:
                print("DEBUG: No dialog is visible on the page.")

            # Maybe it went straight to messaging modal if we have premium or they have open profile
            msg_box = page.locator(
                "textarea[name='message']:visible, textarea#custom-message:visible, div[role='dialog'] textarea:visible"
            ).first
            if msg_box.count() > 0 and msg_box.is_visible():
                try:
                    msg_box.fill(message, timeout=5000)
                    page.wait_for_timeout(1000)
                    send_btn = page.locator(
                        "button[aria-label='Send']:visible, button:has-text('Send'):visible"
                    ).first
                    try:
                        send_btn.evaluate("node => node.click()")
                    except Exception as e:
                        print(f"Evaluate Send error: {e}")
                        send_btn.click(force=True, timeout=5000)

                    print(
                        f"Successfully sent direct message/inmail to {employee['name']}"
                    )
                    log_user_messaged(
                        employee["profile_url"],
                        employee["name"],
                        employee["company"],
                        job["job_id"],
                    )
                    page.wait_for_timeout(random.randint(15000, 30000))
                    return True
                except Exception as e:  # noqa: BLE001
                    print(f"Error sending direct message: {e}")
                    return False

            return False

    except Exception as e:  # noqa: BLE001
        print(f"Error sending message to {employee['name']}: {e}")
        return False
