import os
from playwright.sync_api import sync_playwright

SESSION_DIR = "session"

def manual_login():
    """
    Launches a visible browser for the user to manually log into LinkedIn.
    Once logged in and the user presses Enter in the console, the state is saved.
    """
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR)
        
    print("Launching browser for manual login...")
    print("Please log into LinkedIn in the browser window that opens.")
    print("IMPORTANT: After you have successfully logged in and can see your feed, return to this console and press ENTER to save the session.")
    
    with sync_playwright() as p:
        # We use persistent context so it saves directly to the directory
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False, # Must be false for manual login
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://www.linkedin.com/login")
        
        input("Press ENTER here after you have logged into LinkedIn... ")
        
        # Give it a second to ensure any final cookies are written
        page.wait_for_timeout(2000)
        
        context.close()
        print(f"Session state saved to {SESSION_DIR}/")

if __name__ == "__main__":
    manual_login()
