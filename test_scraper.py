from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

import job_scraper


def test_extract():
    html_content = """
    <html>
    <body>
        <div class="job-search-card" data-entity-urn="urn:li:jobPosting:123456789">
            <a href="https://linkedin.com/jobs/view/123456789" class="base-card__full-link">
                <span class="sr-only">Software Engineer</span>
            </a>
            <div class="base-search-card__info">
                <h3 class="base-search-card__title">Software Engineer</h3>
                <h4 class="base-search-card__subtitle">
                    <a class="hidden-nested-link" href="https://www.linkedin.com/company/acme-corp?trk=public_jobs_jserp-result_job-search-card-subtitle">
                        Acme Corp
                    </a>
                </h4>
            </div>
        </div>
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content(html_content)

            # Mock the `database.is_job_processed` to return False
            job_scraper.is_job_processed = lambda x: False

            card = page.locator("div.job-search-card").first

            job = job_scraper.extract_job_from_card(page, card)

            print("Extracted Job:", job)

            assert job is not None
            assert job["job_id"] == "123456789"
            assert job["title"] == "Software Engineer"
            assert job["company"] == "Acme Corp"
            assert "acme-corp" in job["company_url"]
        finally:
            browser.close()
        print("Extract test passed.")


def test_lambdas():
    # specifically test the BS4 logic that failed before due to non-string classes
    html = """
    <div>
        <h3 class="base-search-card__title">Title</h3>
        <h4 class="base-search-card__subtitle">Subtitle</h4>
        <a href="https://www.linkedin.com/company/test">Link</a>
        <div class=["list", "of", "classes"]>Ignore this</div>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    # This would throw if isinstance(x, str) wasn't there since some classes are lists

    title_elem = soup.find(
        class_=lambda x: (
            x
            and isinstance(x, str)
            and ("title" in x.lower() or "sr-only" in x.lower())
        )
    )
    assert title_elem.get_text() == "Title"

    comp_elem = soup.find(
        class_=lambda x: x and isinstance(x, str) and "subtitle" in x.lower()
    )
    assert comp_elem.get_text() == "Subtitle"

    comp_link = soup.find(
        "a", href=lambda x: x and isinstance(x, str) and "/company/" in x
    )
    assert comp_link is not None
    print("Lambda test passed.")


if __name__ == "__main__":
    test_lambdas()
    test_extract()
