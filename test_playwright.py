from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content("""
        <div class="test">Item 1</div>
        <div class="test">Item 2</div>
    """)
    
    loc1 = page.locator("div.test").nth(0)
    print("nth(0) count:", loc1.count())
    
    loc2 = page.locator("div.test").nth(1)
    print("nth(1) count:", loc2.count())
    
    loc3 = page.locator("div.test").nth(2)
    print("nth(2) count:", loc3.count())
    
    loc4 = page.locator("div.nonexistent").nth(0)
    print("nonexistent nth(0) count:", loc4.count())
    
    browser.close()
