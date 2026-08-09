from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content('<a href="/jobs/view/12345">Job Card</a>')
    
    card = page.locator('nonexistent').first
    
    try:
        val = card.get_attribute('data-job-id', timeout=1000)
        print(f"Attribute value: {val}")
    except Exception as e:
        print(f"Error: {e}")
        
    browser.close()
