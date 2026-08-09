import random
import urllib.parse
import re

from bs4 import BeautifulSoup

from database import is_job_processed

def get_job_search_url(keywords, location, past_24_hours=True, start=0):
    base_url = "https://www.linkedin.com/jobs/search/?"
    params = {
        "keywords": keywords,
        "location": location,
        "f_TPR": "r86400" if past_24_hours else "",
        "start": start
    }
    return base_url + urllib.parse.urlencode({k: v for k, v in params.items() if v or k == "start"})

def load_job_search_page(page, config, start=0):
    """
    Navigates to the jobs page, scrolls to load all listings, and returns the total number of job links found.
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
        
        current_count = page.locator("div.job-card-container, span._983b42c3, a[href*='/jobs/view/']").count()
        if current_count > previous_count:
            previous_count = current_count
            attempts_without_new_jobs = 0
        else:
            attempts_without_new_jobs += 1

    job_cards = page.locator("a[href*='/jobs/view/']").all()
    
    if not job_cards:
        job_cards = page.locator("div._13225c48, span._983b42c3").all()

    print(f"Found {len(job_cards)} job cards on the page.")
    return len(job_cards)

def extract_job_from_card(page, card):
    try:
        try:
            card.scroll_into_view_if_needed(timeout=2000)
            card.click(timeout=2000, force=True)
        except Exception:  # noqa: BLE001, S110
            pass
            
        page.wait_for_timeout(random.randint(1500, 2500))

        job_id = None
        m = re.search(r"currentJobId=(\d+)", page.url)
        if m:
            job_id = m.group(1)

        if not job_id:
            try:
                href = card.get_attribute("href") or ""
                if "/jobs/view/" in href:
                    job_id = href.split("/jobs/view/")[1].split("/")[0].split("?")[0]
            except Exception:
                pass
                
        if not job_id:
            try:
                job_id = card.get_attribute("data-job-id")
            except Exception:
                pass

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
        
        # Method 1: Get it from the header element containing the job view link in the main panel
        try:
            job_title_link = page.locator("a[href*='/jobs/view/'] h2").first
            if job_title_link.count() > 0:
                title = job_title_link.inner_text().strip()
            
            # Method 2: Generic header check in the right panel
            if title == "Unknown Title" or not title:
                possible_titles = page.locator("h1, h2.t-24, h2.jobs-details-top-card__job-title").all()
                for t_elem in possible_titles:
                    t_text = t_elem.inner_text().strip()
                    if t_text and t_text not in ["About the job", "About the role"] and len(t_text) > 3:
                        if "(Verified job)" not in t_text and "Selected" not in t_text:
                            title = t_text
                            break
            
            # Method 3: Try to extract it from the card text itself
            if title == "Unknown Title" or not title:
                card_text = card.inner_text().strip()
                if card_text and len(card_text.split('\n')[0]) > 3:
                    title = card_text.split('\n')[0].strip()
        except Exception:
            pass

        if "Selected," in title:
            title = title.replace("Selected,", "").strip()
        if "(Verified job)" in title:
            title = title.replace("(Verified job)", "").strip()

        if is_job_processed(job_id):
            print(f"Skipping job {job_id} ({title}) - already processed.")
            return None

        # Extract company name
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

        # Extract full job description
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

        if title == "Unknown Title" and company == "Unknown Company":
            return None

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
