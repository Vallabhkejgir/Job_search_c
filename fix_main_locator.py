with open('main.py', 'r') as f:
    content = f.read()

old_loop = """            # 2. Interleaved Process: Extract -> Search Employees -> Message
            for i in range(num_cards):
                # Dynamically locate card element in search results list
                card = page.locator("div.base-search-card, div.job-search-card").nth(i)
                if card.count() == 0:
                    card = page.locator("a[href*='/jobs/view/']").nth(i)
                if card.count() == 0:
                    card = page.locator("div.job-card-container, div._13225c48, span._983b42c3").nth(i)"""

new_loop = """            # Determine the primary locator for this page's cards
            card_selector = "div.base-search-card, div.job-search-card"
            if page.locator(card_selector).count() == 0:
                card_selector = "a[href*='/jobs/view/']"
                if page.locator(card_selector).count() == 0:
                    card_selector = "div.job-card-container, div._13225c48, span._983b42c3"

            # 2. Interleaved Process: Extract -> Search Employees -> Message
            for i in range(num_cards):
                # Dynamically locate card element in search results list
                card = page.locator(card_selector).nth(i)"""

if old_loop in content:
    content = content.replace(old_loop, new_loop)
    with open('main.py', 'w') as f:
        f.write(content)
    print("Fixed main.py locator logic")
else:
    print("Could not find old loop")
