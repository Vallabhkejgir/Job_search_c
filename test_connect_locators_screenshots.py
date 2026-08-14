import os

from playwright.sync_api import sync_playwright

import config
import messenger

HTML_SCENARIO_2_MORE_CONNECT = """
<!DOCTYPE html>
<html>
<head>
    <title>LinkedIn Profile - More Connect</title>
    <style>
        body { font-family: sans-serif; padding: 20px; background: #f3f2ef; }
        main { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 5px rgba(0,0,0,0.1); width: 600px; margin: 0 auto; position: relative;}
        .profile { display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
        .avatar { width: 100px; height: 100px; background: #ccc; border-radius: 50%; }
        button { cursor: pointer; border: none; padding: 8px 16px; border-radius: 16px; font-weight: bold; }
        #more-btn { background: white; color: #666; border: 1px solid #666; }
        #more-btn:hover { background: #eee; }
        
        .artdeco-dropdown__content {
            position: absolute; top: 120px; left: 140px; background: white; border: 1px solid #ddd; border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 150px;
        }
        .artdeco-dropdown__content ul { list-style: none; padding: 0; margin: 0; }
        .artdeco-dropdown__content li { padding: 10px 15px; cursor: pointer; }
        .artdeco-dropdown__content li:hover { background: #f3f2ef; }
        
        #modal {
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            width: 400px; z-index: 100;
        }
        #modal textarea { width: 100%; height: 100px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; padding: 8px; box-sizing: border-box;}
        #send-btn { background: #0a66c2; color: white; float: right;}
        #add-note-btn { background: white; color: #666; border: 1px solid #666; }
        
        #overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 50; display: none; }
        #success { margin-top: 20px; padding: 10px; background: #d4edda; color: #155724; border-radius: 4px; text-align: center; }
    </style>
</head>
<body>
    <main>
        <div class="profile">
            <div class="avatar"></div>
            <div>
                <h2>Jane Doe</h2>
                <p>Software Engineer at TestCorp</p>
                <button aria-label="More actions" id="more-btn">More</button>
            </div>
        </div>
    </main>
    <div id="dropdown" class="artdeco-dropdown__content" style="display: none;">
        <ul>
            <li><span>Send in a message</span></li>
            <li id="connect-btn-li"><span>Connect</span></li>
            <li><span>Report/Block</span></li>
        </ul>
    </div>
    <div id="overlay"></div>
    <div id="modal" style="display: none;">
        <h3>Connect with Jane</h3>
        <p>You can add a note to personalize your invitation.</p>
        <button aria-label="Add a note" id="add-note-btn">Add a note</button>
        <div id="note-section" style="display:none;">
            <textarea name="message" id="message-box"></textarea>
            <button aria-label="Send now" id="send-btn">Send</button>
        </div>
    </div>
    <script>
        document.getElementById('more-btn').addEventListener('click', () => {
            document.getElementById('dropdown').style.display = 'block';
        });
        document.getElementById('dropdown').addEventListener('click', (e) => {
            if (e.target.textContent.includes('Connect')) {
                document.getElementById('dropdown').style.display = 'none';
                document.getElementById('overlay').style.display = 'block';
                document.getElementById('modal').style.display = 'block';
            }
        });
        document.getElementById('add-note-btn').addEventListener('click', (e) => {
            e.target.style.display = 'none';
            document.getElementById('note-section').style.display = 'block';
        });
        document.getElementById('send-btn').addEventListener('click', () => {
            document.getElementById('overlay').style.display = 'none';
            document.getElementById('modal').style.display = 'none';
            document.querySelector('main').innerHTML += '<div id="success">✅ Connection Request Sent!</div>';
        });
    </script>
</body>
</html>
"""

messenger.log_user_messaged = lambda *args, **kwargs: None


def run_test_scenario(p, html_content, name):
    print(f"Running scenario: {name}")
    browser = p.chromium.launch(headless=True)
    try:
        page = browser.new_page()
        page.set_content(html_content)

        page.goto = lambda url, **kwargs: None
        page.wait_for_timeout = lambda timeout: None

        employee = {
            "name": "Jane Doe",
            "profile_url": "https://linkedin.com/in/janedoe",
            "company": "TestCorp",
        }
        job = {"title": "Engineer", "company": "TestCorp", "job_id": "1"}
        config.DRY_RUN = False

        # We will override page.locator.click to take screenshots right before clicking
        # Actually, we can just patch messenger.send_connection_request locally if we wanted,
        # or just let playwright do it. Wait, the easiest way is to wrap it.

        # Take initial screenshot
        output_dir = "/tmp/no-mistakes-evidence/01KZNW8DAQMR9NY813X2R5XQYH"
        if os.path.exists(output_dir):
            page.screenshot(path=os.path.join(output_dir, "01_initial_profile.png"))

        success = messenger.send_connection_request(
            page, employee, job, "I am great", config
        )

        # Take final screenshot
        if os.path.exists(output_dir):
            page.screenshot(path=os.path.join(output_dir, "02_final_success.png"))

        if not success:
            print(f"❌ Scenario {name} failed: function returned False")
        else:
            print(f"✅ Scenario {name} passed!")
    finally:
        browser.close()


with sync_playwright() as p:
    run_test_scenario(
        p, HTML_SCENARIO_2_MORE_CONNECT, "Connect inside More menu with visual flow"
    )
