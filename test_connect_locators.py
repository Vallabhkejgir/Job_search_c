from playwright.sync_api import sync_playwright

import config
import messenger

HTML_SCENARIO_2_MORE_CONNECT = """
<!DOCTYPE html>
<html>
<head>
    <title>LinkedIn Profile - More Connect</title>
</head>
<body>
    <main>
        <section>
            <h1>Jane Doe</h1>
            <p>Engineer at TestCorp</p>
        </section>
        <button aria-label="More actions" id="more-btn">More</button>
    </main>
    <div id="dropdown" class="artdeco-dropdown__content" style="display: none;">
        <ul>
            <li><button id="connect-btn"><span>Connect</span></button></li>
        </ul>
    </div>
    <div id="modal" style="display: none;">
        <button aria-label="Add a note" id="add-note-btn">Add a note</button>
        <textarea name="message" id="message-box"></textarea>
        <button aria-label="Send now" id="send-btn">Send</button>
    </div>
    <script>
        document.getElementById('more-btn').addEventListener('click', () => {
            console.log('more clicked');
            document.getElementById('dropdown').style.display = 'block';
        });
        document.getElementById('dropdown').addEventListener('click', (e) => {
            console.log('dropdown clicked on', e.target.tagName);
            if (e.target.textContent.includes('Connect')) {
                document.getElementById('modal').style.display = 'block';
            }
        });
        document.getElementById('send-btn').addEventListener('click', () => {
            console.log('send clicked');
            document.body.innerHTML += '<div id="success">Message Sent!</div>';
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
        page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
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

        success = messenger.send_connection_request(
            page, employee, job, "I am great", config
        )

        if not success:
            print(f"❌ Scenario {name} failed: function returned False")
        else:
            print(f"✅ Scenario {name} passed!")
    finally:
        browser.close()


with sync_playwright() as p:
    run_test_scenario(p, HTML_SCENARIO_2_MORE_CONNECT, "Connect inside More menu")
