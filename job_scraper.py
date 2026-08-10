import random
import re
import urllib.parse

from bs4 import BeautifulSoup

from database import is_job_processed


def get_job_search_url(keywords, location, past_24_hours=True, start=0):
    base_url = "https://www.linkedin.com/jobs/search/?"
    params = {
        "keywords": keywords,
        "location": location,
        "f_TPR": "r86400" if past_24_hours else "",
        "start": start,
    }
    return base_url + urllib.parse.urlencode(
        {k: v for k, v in params.items() if v or k == "start"}
    )


def load_job_search_page(page, config, start=0):
    """
    Navigates to the jobs page, scrolls to load all listings, and returns the total number of job links found and the card selector.
    """
    url = get_job_search_url(
        config.SEARCH_KEYWORDS,
        config.SEARCH_LOCATION,
        config.PAST_24_HOURS_FILTER,
        start,
    )
    print(f"Navigating to job search: {url}")

    # Use domcontentloaded or a longer timeout for the heavy LinkedIn jobs page
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(random.randint(3000, 5000))

    # Scroll the job list panel to trigger lazy-loading of all job cards
    print("Scrolling job search results to load all postings...")
    previous_count = 0
    attempts_without_new_jobs = 0

    while attempts_without_new_jobs < 3:
        page.mouse.wheel(0, 1500)
        page.evaluate("""
            var element = document.querySelector('.jobs-search-results-list') || document.querySelector('main') || document.scrollingElement;
            if(element) element.scrollBy(0, 1500);
            window.scrollBy(0, 1500);
        """)
        page.wait_for_timeout(random.randint(1500, 2500))

        current_count = page.locator(
            "div.base-search-card, div.job-card-container, a[href*='/jobs/view/']"
        ).count()
        if current_count > previous_count:
            previous_count = current_count
            attempts_without_new_jobs = 0
        else:
            attempts_without_new_jobs += 1

    # First try the newer/unauthenticated layout cards
    job_cards = page.locator("div.base-search-card, div.job-search-card").all()
    card_selector = "div.base-search-card, div.job-search-card"

    if not job_cards:
        job_cards = page.locator("a[href*='/jobs/view/']").all()
        card_selector = "a[href*='/jobs/view/']"

    if not job_cards:
        job_cards = page.locator(
            "div.job-card-container, div._13225c48, span._983b42c3"
        ).all()
        card_selector = "div.job-card-container, div._13225c48, span._983b42c3"

    print(f"Found {len(job_cards)} job cards on the page.")
    return len(job_cards), card_selector


def extract_job_from_card(page, card):
    try:
        try:
            card.scroll_into_view_if_needed(timeout=2000)
            card.click(timeout=2000, force=True)
        except Exception:  # noqa: BLE001, S110
            pass

        page.wait_for_timeout(random.randint(1500, 2500))

        job_id = None

        # 1. New UI: check data-entity-urn on the card
        try:
            urn = card.get_attribute("data-entity-urn", timeout=1000)
            if urn and "jobPosting" in urn:
                job_id = urn.split(":")[-1]
        except Exception:  # noqa: BLE001, S110
            pass

        # 2. Try URL matching
        if not job_id:
            m = re.search(r"currentJobId=(\d+)", page.url)
            if m:
                job_id = m.group(1)

        # 3. Try getting it from the href slug
        if not job_id:
            try:
                href = card.get_attribute("href", timeout=1000) or ""
                if "/jobs/view/" in href:
                    # Match numeric ID at the end of the slug: ai-engineer-at-company-1234567890
                    m = re.search(r"-(\d{9,11})\b", href)
                    if m:
                        job_id = m.group(1)
                    else:
                        job_id = (
                            href.split("/jobs/view/")[1].split("/")[0].split("?")[0]
                        )
            except Exception:  # noqa: BLE001, S110
                pass

        # 4. Try data-job-id attribute
        if not job_id:
            try:
                job_id = card.get_attribute("data-job-id", timeout=1000)
            except Exception:  # noqa: BLE001, S110
                pass

        # 5. Try finding it in page content
        if not job_id:
            html = page.content()
            m = re.search(r'"jobPosting":\{"jobPostingId":(\d+)', html)
            if m:
                job_id = m.group(1)

        if not job_id:
            print("Could not find job ID.")
            return None

        # Fix Title Extraction for the new UI
        title = "Unknown Title"
        company = "Unknown Company"
        company_url = None

        # New Unauthenticated Layout
        try:
            html = card.inner_html(timeout=1000)
            soup = BeautifulSoup(html, "html.parser")

            title_elem = soup.find(
                class_=lambda x: x
                and isinstance(x, str)
                and ("title" in x.lower() or "sr-only" in x.lower())
            )
            if title_elem:
                title = title_elem.get_text(strip=True)

            comp_elem = soup.find(
                class_=lambda x: x and isinstance(x, str) and "subtitle" in x.lower()
            )
            if comp_elem:
                company = comp_elem.get_text(strip=True)

            comp_link = soup.find(
                "a", href=lambda x: x and isinstance(x, str) and "/company/" in x
            )
            if comp_link:
                company_url = comp_link["href"].split("?")[0]
        except Exception:  # noqa: BLE001, S110
            pass

        # Old/Authenticated Layout fallbacks
        try:
            if title == "Unknown Title" or not title:
                job_title_link = page.locator("a[href*='/jobs/view/'] h2").first
                if job_title_link.count() > 0:
                    title = job_title_link.inner_text().strip()

                if title == "Unknown Title" or not title:
                    possible_titles = page.locator(
                        "h1, h2.t-24, h2.jobs-details-top-card__job-title"
                    ).all()
                    for t_elem in possible_titles:
                        t_text = t_elem.inner_text().strip()
                        if (
                            t_text
                            and t_text not in ["About the job", "About the role"]
                            and len(t_text) > 3
                        ) and (
                            "(Verified job)" not in t_text and "Selected" not in t_text
                        ):
                            title = t_text
                            break

                if title == "Unknown Title" or not title:
                    card_text = card.inner_text().strip()
                    if card_text and len(card_text.split("\n")[0]) > 3:
                        title = card_text.split("\n")[0].strip()
        except Exception:  # noqa: BLE001, S110
            pass

        if "Selected," in title:
            title = title.replace("Selected,", "").strip()
        if "(Verified job)" in title:
            title = title.replace("(Verified job)", "").strip()

        if is_job_processed(job_id):
            print(f"Skipping job {job_id} - already processed.")
            return None

        try:
            if company == "Unknown Company" or not company_url:
                company_link = page.locator('a[href*="/company/"]').first
                if company_link.count() > 0:
                    href = company_link.get_attribute("href", timeout=1000)
                    if href and "/company/" in href:
                        company_url = href.split("?")[0]
                        if company == "Unknown Company":
                            company = company_link.inner_text().strip()
        except Exception:  # noqa: BLE001, S110
            pass

        # Extract full job description
        description = ""
        about_h2 = page.locator(
            "h2:has-text('About the job'), h2:has-text('About the role')"
        ).first
        if about_h2.count() > 0:
            try:
                desc_container = about_h2.locator("xpath=parent::*/parent::*").first
                if desc_container.count() > 0:
                    description = desc_container.inner_text().strip()
            except Exception:  # noqa: BLE001, S110
                pass

        if not description:
            desc_elem = page.locator(
                "#job-details, .jobs-description, .jobs-search__job-details"
            ).first
            if desc_elem.count() > 0:
                soup = BeautifulSoup(desc_elem.inner_html(), "html.parser")
                description = soup.get_text(separator="\n", strip=True)

        if title == "Unknown Title" and company == "Unknown Company":
            return None

        print(f"Extracted: {title} at {company} (ID: {job_id})")
        return {
            "job_id": job_id,
            "title": title,
            "company": company,
            "company_url": company_url,
            "description": description,
            "url": f"https://www.linkedin.com/jobs/view/{job_id}",
        }

    except Exception as e:  # noqa: BLE001
        print(f"Error extracting job card: {e}")
        return None
