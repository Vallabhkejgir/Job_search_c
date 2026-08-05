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

def scrape_jobs(page, config):
    """
    Navigates to the jobs page, scrolls to load listings, and extracts job details.
    """
    url = get_job_search_url(config.SEARCH_KEYWORDS, config.SEARCH_LOCATION, config.PAST_24_HOURS_FILTER)
    print(f"Navigating to job search: {url}")

    # Use domcontentloaded or a longer timeout for the heavy LinkedIn jobs page
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(random.randint(3000, 5000))
    
    jobs = []
    
    # Wait for job list container
    try:
        # Fallback selectors for different LinkedIn layouts
        try:
            page.wait_for_selector(".scaffold-layout__list", timeout=10000)
        except:
            try:
                page.wait_for_selector(".scaffold-layout__list-container", timeout=10000)
            except:
                page.wait_for_selector(".job-card-container", timeout=10000)
    except Exception as e:
        print("Could not find job list container. Maybe no results or blocked by captcha/login wall.")
        return jobs
        
    # Scroll the job list panel to load more jobs (LinkedIn uses lazy loading)
    for _ in range(3):
        page.evaluate("""
            var element = document.querySelector('.jobs-search-results-list');
            if(element) element.scrollBy(0, 1000);
        """)
        page.wait_for_timeout(random.randint(1000, 2000))
        
    # Extract job cards
    job_cards = page.locator(".job-card-container").all()
    print(f"Found {len(job_cards)} job cards on the page.")
    
    for card in job_cards:
        try:
            # Click the card to load details on the right panel
            card.scroll_into_view_if_needed()
            card.click()
            page.wait_for_timeout(random.randint(2000, 3500))
            
            # Extract basic info
            job_id = card.get_attribute("data-job-id")
            if not job_id:
                continue
                
            if is_job_processed(job_id):
                print(f"Skipping job {job_id} - already processed.")
                continue
                
            title_elem = card.locator(".job-card-list__title, .job-card-container__title")
            title = title_elem.first.inner_text().strip() if title_elem.count() > 0 else "Unknown Title"

            company_elem = card.locator(".job-card-container__primary-description, .job-card-container__company-name")
            company = company_elem.first.inner_text().strip() if company_elem.count() > 0 else "Unknown Company"
            
            # Extract full description from the right panel
            desc_locator = page.locator("#job-details, .jobs-description").first
            if desc_locator.count() > 0:
                # Use BeautifulSoup to get clean text without tons of HTML tags
                html_content = desc_locator.inner_html()
                soup = BeautifulSoup(html_content, "html.parser")
                description = soup.get_text(separator="\n", strip=True)
            else:
                description = ""
                
            jobs.append({
                "job_id": job_id,
                "title": title,
                "company": company,
                "description": description,
                "url": f"https://www.linkedin.com/jobs/view/{job_id}"
            })
            
            print(f"Extracted: {title} at {company}")
            
            # Don't extract too many in one go to avoid limits
            if len(jobs) >= 10:
                break
                
        except Exception as e:
            print(f"Error extracting a job card: {e}")
            continue
            
    return jobs
