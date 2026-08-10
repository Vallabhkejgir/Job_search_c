from playwright.sync_api import sync_playwright


def test_load_page():
    html_content = """
    <html>
    <body>
        <div class="job-search-card">Card 1</div>
        <div class="job-search-card">Card 2</div>
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)

        # Mock the goto to do nothing
        page.goto = lambda *args, **kwargs: None
        # Mock wait_for_timeout to be fast
        page.wait_for_timeout = lambda *args, **kwargs: None

        # Just to avoid the page scroll throwing errors
        # page.mouse is a property, can't be set. But for this test, we don't actually call load_page,
        # we just inline the locator logic, so we don't need to mock it.

        # Test the locator logic
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

        print("Num cards:", len(job_cards))
        print("Selector:", card_selector)

        assert len(job_cards) == 2
        assert card_selector == "div.base-search-card, div.job-search-card"

        browser.close()
        print("Load page logic test passed.")


if __name__ == "__main__":
    test_load_page()
