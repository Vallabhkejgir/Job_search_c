import random
import urllib.parse

from bs4 import BeautifulSoup

from database import is_job_processed


def get_job_search_url(keywords, location, past_24_hours=True, start=0):
    base_url = "https://www.linkedin.com/jobs/search/?"
    params = {
        "keywords": keywords,
        "location": location,
        "f_TPR": "r86400" if past_24_hours else "", # r86400 is LinkedIn's code for past 24h (86400 seconds)
        "start": start
    }
    return base_url + urllib.parse.urlencode({k: v for k, v in params.items() if v or k == "start"})

def load_job_search_page(page, config, start=0):
    """
    Navigates to the jobs page, scrolls to load all listings, and returns the total number of job cards found.
    """
    url = get_job_search_url(config.SEARCH_KEYWORDS, config.SEARCH_LOCATION, config.PAST_24_HOURS_FILTER, start)
    print(f"Navigating to job search: {url}")

    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)

    # Scroll the job list panel to trigger lazy-loading of all job cards
    print("Scrolling job search results to load all postings...")
    previous_count = 0
    attempts_without_new_jobs = 0
    
    while attempts_without_new_jobs < 3:
        page.mouse.wheel(0, 1500)
        page.evaluate("""
            var element = document.querySelector('.jobs-search-results-list') || document.querySelector('main');
            if(element) element.scrollBy(0, 1500);
        """)
        page.wait_for_timeout(random.randint(1500, 2500))
        
        current_count = page.locator("div._13225c48, span._983b42c3").count()
        if current_count > previous_count:
            previous_count = current_count
            attempts_without_new_jobs = 0
        else:
            attempts_without_new_jobs += 1

    # Extract job card elements
    job_cards = page.locator("div._13225c48, span._983b42c3").all()
    print(f"Found {len(job_cards)} job cards on the page.")
    return len(job_cards)

def extract_job_from_card(page, card):
    try:
        import re

        # Extract title and raw text before clicking
        txt = card.inner_text().strip()
        lines = [l.strip() for l in txt.split("\n") if l.strip()]
        if not lines:
            return None

        first_line = lines[0]
        # Ignore non-job filter or navigation text
        if first_line in ["Home", "Jobs", "Past 24 hours", "Remote", "Gen AI", "LLM", "Data", "Research & Development", "Easy Apply", "Experience level", "Employment type", "Company", "Under 10 applicants", "In my network", "How promoted jobs are ranked", "Are these results helpful?", "About the job", "See how you compare to other applicants"]:
            return None

        if len(first_line) < 3 or first_line.startswith(("Posted", "Be an early")):
            return None

        title = first_line
        if "Selected," in title:
            title = title.replace("Selected,", "").strip()
        if "(Verified job)" in title:
            title = title.replace("(Verified job)", "").strip()

        # Click the card to load details into the right panel
        try:
            card.scroll_into_view_if_needed(timeout=2000)
            card.click(timeout=2000)
        except Exception:  # noqa: BLE001, S110
            pass
        page.wait_for_timeout(random.randint(1200, 2000))

        # Extract basic info (job ID from current URL or data attribute)
        job_id = None
        m = re.search(r"currentJobId=(\d+)", page.url)
        if m:
            job_id = m.group(1)

        if not job_id:
            job_id = card.get_attribute("data-job-id")

        if not job_id:
            href = card.get_attribute("href") or ""
            if "/jobs/view/" in href:
                job_id = href.split("/jobs/view/")[1].split("/")[0].split("?")[0]

        if not job_id:
            return None

        if is_job_processed(job_id):
            print(f"Skipping job {job_id} ({title}) - already processed.")
            return None

        # Extract company name & company URL from right-side detail panel header
        company = "Unknown Company"
        company_url = None

        company_link = page.locator("a[href*='/company/']").first
        if company_link.count() > 0:
            c_text = company_link.inner_text().strip()
            if c_text:
                company = c_text
            href = company_link.get_attribute("href")
            if href and "/company/" in href:
                company_url = href.split("?")[0]

        if company == "Unknown Company" and len(lines) > 1:
            potential_comp = lines[1].replace("(Verified job)", "").strip()
            if potential_comp != title and not potential_comp.startswith("Posted"):
                company = potential_comp

        # Extract full job description from right panel
        description = ""
        about_h2 = page.locator("h2:has-text('About the job'), h2:has-text('About the role')").first
        if about_h2.count() > 0:
            try:
                desc_container = about_h2.locator("xpath=parent::*/parent::*").first
                if desc_container.count() > 0:
                    description = desc_container.inner_text().strip()
            except Exception:  # noqa: BLE001, S110
                pass

        if not description:
            desc_elem = page.locator("#job-details, .jobs-description, .jobs-search__job-details").first
            if desc_elem.count() > 0:
                soup = BeautifulSoup(desc_elem.inner_html(), "html.parser")
                description = soup.get_text(separator="\n", strip=True)

        print(f"Extracted: {title} at {company} (ID: {job_id})")
        return {
            "job_id": job_id,
            "title": title,
            "company": company,
            "company_url": company_url,
            "description": description,
            "url": f"https://www.linkedin.com/jobs/view/{job_id}"
        }

    except Exception as e:  # noqa: BLE001
        print(f"Error extracting job card: {e}")
        return None
