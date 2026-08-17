from playwright.sync_api import sync_playwright
import config
import messenger

messenger.log_user_messaged = lambda *args, **kwargs: None

HTML_SCENARIO_MORE_CONNECT = """
<!DOCTYPE html>
<html>
<head><title>More Connect</title></head>
<body>
    <main><section><h1>Jane Doe</h1><p>TestCorp</p></section><button aria-label="More actions" id="more-btn">More</button></main>
    <div id="dropdown" class="artdeco-dropdown__content" style="display: none;"><ul><li><button id="connect-btn"><span>Connect</span></button></li></ul></div>
    <div id="modal" role="dialog" style="display: none;">
        <button aria-label="Add a note" id="add-note-btn">Add a note</button>
        <textarea name="message" id="message-box"></textarea>
        <button aria-label="Send now" id="send-btn">Send</button>
    </div>
    <script>
        document.getElementById('more-btn').addEventListener('click', () => { document.getElementById('dropdown').style.display = 'block'; });
        document.getElementById('dropdown').addEventListener('click', (e) => { if (e.target.textContent.includes('Connect')) document.getElementById('modal').style.display = 'block'; });
        document.getElementById('send-btn').addEventListener('click', () => { document.body.innerHTML += '<div id="success">Message Sent!</div>'; });
    </script>
</body>
</html>
"""

HTML_SCENARIO_CHAT_BUBBLE = """
<!DOCTYPE html>
<html>
<head><title>Chat Bubble</title></head>
<body>
    <aside class="msg-overlay-container">
        <header><button class="msg-overlay-bubble-header__control--close-btn" id="close-chat">Close</button></header>
    </aside>
    <textarea name="message" id="wrong-message-box">Wrong textarea</textarea>
    <main><section><h1>Jane Doe</h1><p>TestCorp</p></section><button aria-label="Connect" id="connect-btn">Connect</button></main>
    <div id="modal" class="artdeco-modal" style="display: none;">
        <button aria-label="Add a note" id="add-note-btn">Add a note</button>
        <textarea name="message" id="right-message-box"></textarea>
        <button aria-label="Send now" id="send-btn">Send</button>
    </div>
    <script>
        let chatClosed = false;
        document.getElementById('close-chat').addEventListener('click', () => { chatClosed = true; document.querySelector('aside').style.display = 'none'; console.log('Chat closed!'); });
        document.getElementById('connect-btn').addEventListener('click', () => { document.getElementById('modal').style.display = 'block'; });
        document.getElementById('send-btn').addEventListener('click', () => {
            const wrongText = document.getElementById('wrong-message-box').value;
            const rightText = document.getElementById('right-message-box').value;
            if (chatClosed && wrongText === 'Wrong textarea' && rightText.includes('Hi Jane')) {
                console.log('Success! Chat was closed and correct textarea was filled.');
            } else {
                console.log('Failed! Chat closed:', chatClosed, 'Wrong text:', wrongText, 'Right text:', rightText);
            }
        });
    </script>
</body>
</html>
"""

HTML_SCENARIO_NAME_VERIFY = """
<!DOCTYPE html>
<html>
<head><title>Name Verify</title></head>
<body>
    <main><section><h1>Real Jane Doe is open to work</h1><p>TestCorp</p></section><button aria-label="Connect" id="connect-btn">Connect</button></main>
    <div id="modal" role="dialog" style="display: none;">
        <button aria-label="Add a note" id="add-note-btn">Add a note</button>
        <textarea name="message" id="message-box"></textarea>
        <button aria-label="Send now" id="send-btn">Send</button>
    </div>
    <script>
        document.getElementById('connect-btn').addEventListener('click', () => { document.getElementById('modal').style.display = 'block'; });
        document.getElementById('send-btn').addEventListener('click', () => {
            const text = document.getElementById('message-box').value;
            if (text.includes('Hi Real')) {
                console.log('Name verified correctly!');
            } else {
                console.log('Name verification failed! Text:', text);
            }
        });
    </script>
</body>
</html>
"""

def run_test_scenario(p, html_content, name):
    print(f"\nRunning scenario: {name}")
    browser = p.chromium.launch(headless=True)
    try:
        page = browser.new_page()
        logs = []
        page.on("console", lambda msg: logs.append(msg.text))
        page.set_content(html_content)

        page.goto = lambda url, **kwargs: None
        page.wait_for_timeout = lambda timeout: None

        employee = {
            "name": "Old Name",
            "profile_url": "https://linkedin.com/in/janedoe",
            "company": "TestCorp",
        }
        job = {"title": "Engineer", "company": "TestCorp", "job_id": "1"}
        config.DRY_RUN = False

        success = messenger.send_connection_request(
            page, employee, job, "I am great", config
        )

        for log in logs:
            print(f"Browser Console: {log}")

        if not success:
            print(f"❌ Scenario {name} failed: function returned False")
        else:
            print(f"✅ Scenario {name} passed!")
    finally:
        browser.close()

with sync_playwright() as p:
    run_test_scenario(p, HTML_SCENARIO_MORE_CONNECT, "Connect inside More menu")
    run_test_scenario(p, HTML_SCENARIO_CHAT_BUBBLE, "Close chat bubble & scope textarea")
    run_test_scenario(p, HTML_SCENARIO_NAME_VERIFY, "Verify actual name on profile")
