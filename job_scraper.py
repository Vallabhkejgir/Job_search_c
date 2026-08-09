import urllib.parse
import time
import random
from bs4 import BeautifulSoup
from database import is_job_processed

def get_job_search_url(keywords, location, past_24_hours=True):
    base_url = "https://www.linkedin.com/jobs/search/?"
    params = {
        "keywords": keywords,
        "location": location,
        "f_TPR": "r86400" if past_24_hours else "", # r86400 is LinkedIn's code for past 24h (86400 seconds)
    }
    return base_url + urllib.parse.urlencode({k: v for k, v in params.items() if v})

def load_job_search_page(page, config):
    """
    Navigates to the jobs page, scrolls to load listings, and returns the total number of job cards found.
    """
    url = get_job_search_url(config.SEARCH_KEYWORDS, config.SEARCH_LOCATION, config.PAST_24_HOURS_FILTER)
    print(f"Navigating to job search: {url}")

    # Use domcontentloaded or a longer timeout for the heavy LinkedIn jobs page
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(random.randint(3000, 5000))

    # Wait for job list container
    try:
        # Fallback selectors for different LinkedIn layouts
        try:
            page.wait_for_selector(".scaffold-layout__list", timeout=5000)
        except:
            try:
                page.wait_for_selector(".scaffold-layout__list-container", timeout=5000)
            except:
                try:
                    page.wait_for_selector(".job-card-container", timeout=5000)
                except:
                    # In newer LinkedIn UI layouts, job items are loaded inside the main results panel
                    page.wait_for_selector("a[href*='/jobs/view/'], div[class*='jobs-search'], main", timeout=5000)
    except Exception as e:
        print("Could not find job list container. Maybe no results or blocked by captcha/login wall.")
        return 0

    # Scroll the job list panel to load more jobs (LinkedIn uses lazy loading)
    for _ in range(8):
        page.evaluate("""
            var element = document.querySelector('.jobs-search-results-list') || document.querySelector('main');
            if(element) element.scrollBy(0, 1500);
        """)
        page.wait_for_timeout(random.randint(1500, 2500))

    # Extract job cards (support both legacy class and clickable links / containers in new UI)
    job_cards_count = page.locator("a[href*='/jobs/view/']").count()
    print(f"Found {job_cards_count} job cards on the page.")
    return job_cards_count

def extract_job_from_card(page, card):
    try:
        # Extract title and info BEFORE clicking
        title = "Unknown Title"
        try:
            raw_txt = card.inner_text().strip()
            if raw_txt and raw_txt not in ["On-site", "Full-time", "Hybrid", "Remote", "Easy Apply"]:
                title = raw_txt
        except Exception as e:
            pass

        # Extract basic info
        job_id = card.get_attribute("data-job-id")
        if not job_id:
            # Fallback to extract job ID from href if element is an <a> tag
            href = card.get_attribute("href") or ""
            if "/jobs/view/" in href:
                job_id = href.split("/jobs/view/")[1].split("/")[0].split("?")[0]
            elif "currentJobId=" in href:
                import re
                m = re.search(r"currentJobId=(\d+)", href)
                if m:
                    job_id = m.group(1)

        # Click the card to load details on the right panel
        card.scroll_into_view_if_needed()
        card.click()
        page.wait_for_timeout(random.randint(2000, 3500))

        if not job_id:
            # Fallback: inspect page URL or right panel for job ID
            import re
            m = re.search(r"currentJobId=(\d+)", page.url)
            if m:
                job_id = m.group(1)

        if not job_id:
            return None

        if is_job_processed(job_id):
            print(f"Skipping job {job_id} - already processed.")
            return None

        if title == "Unknown Title" or not title:
            # Fallback to the span class containing the title in the new UI
            span_elem = page.locator("span._983b42c3").first
            if span_elem.count() > 0:
                raw_t = span_elem.inner_text().strip()
                if "Selected," in raw_t:
                    raw_t = raw_t.replace("Selected,", "").strip()
                if "(Verified job)" in raw_t:
                    raw_t = raw_t.replace("(Verified job)", "").strip()
                title = raw_t

        company_elem = page.locator(".job-details-jobs-unified-top-card__company-name, .job-details-jobs-unified-top-card__primary-description, a[href*='/company/']").first
        company = company_elem.inner_text().strip() if company_elem.count() > 0 else "Unknown Company"

        # Attempt to extract company URL from the card first
        company_link = company_elem.locator("a").first
        company_url = None
        if company_link.count() > 0:
            href = company_link.get_attribute("href")
            if href and "/company/" in href:
                company_url = href.split("?")[0]

        # If not found, check the right panel's header
        if not company_url:
            # The right panel often has the company logo wrapped in an 'a' tag linking to the company
            panel_link = page.locator(".job-details-jobs-unified-top-card__company-name a, .job-details-jobs-unified-top-card__primary-description a").first
            if panel_link.count() > 0:
                href = panel_link.get_attribute("href")
                if href and "/company/" in href:
                    company_url = href.split("?")[0]

        # Final fallback: generic LinkedIn link in the detail panel
        if not company_url:
            # Look inside the right panel specifically for any company link
            generic_link = page.locator("#job-details a[href*='/company/'], .job-view-layout a[href*='/company/']").first
            if generic_link.count() > 0:
                href = generic_link.get_attribute("href")
                if href and "/company/" in href:
                    company_url = href.split("?")[0]

        # Extract full description from the right panel
        desc_locator = page.locator("#job-details, .jobs-description").first
        if desc_locator.count() > 0:
            # Use BeautifulSoup to get clean text without tons of HTML tags
            html_content = desc_locator.inner_html()
            soup = BeautifulSoup(html_content, "html.parser")
            description = soup.get_text(separator="\n", strip=True)
        else:
            description = ""

        print(f"Extracted: {title} at {company}")
        return {
            "job_id": job_id,
            "title": title,
            "company": company,
            "company_url": company_url,
            "description": description,
            "url": f"https://www.linkedin.com/jobs/view/{job_id}"
        }

    except Exception as e:
        print(f"Error extracting a job card: {e}")
        return None
