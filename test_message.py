import config
import database
from messenger import send_connection_request


def mock_log_user_messaged(url, name, company, job_id):
    pass


database.log_user_messaged = mock_log_user_messaged


def test_user_introduction_env():
    # Mock page
    class MockPage:
        def goto(self, url, **kwargs):
            pass

        def wait_for_timeout(self, timeout):
            pass

        def get_by_role(self, role, name=None, exact=False):
            return self

        def locator(self, loc):
            return self

        def is_visible(self):
            return True

        def click(self):
            pass

        def fill(self, text):
            pass

    employee = {
        "name": "John Doe",
        "profile_url": "https://linkedin.com/in/johndoe",
        "company": "Acme Corp",
    }
    job = {"title": "Software Engineer", "company": "Acme Corp", "job_id": "123"}
    ai_pitch = "I know Python."

    # Set custom user intro
    config.USER_INTRODUCTION = "I am an expert."
    config.DRY_RUN = True

    # Capture print output
    import sys
    from io import StringIO

    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    # We also need to patch messenger's log_user_messaged
    import messenger

    messenger.log_user_messaged = mock_log_user_messaged

    send_connection_request(MockPage(), employee, job, ai_pitch, config)

    sys.stdout = old_stdout
    output = mystdout.getvalue()

    print("OUTPUT:")
    print(output)

    assert "I am an expert." in output
    assert "I know Python." not in output
    assert "[Target] Contact: John Doe" in output
    assert "[DRY RUN] Skipping send to John Doe" in output

    print("Test passed!")


import os
from unittest.mock import patch


class MockLocator:
    def __init__(self, elements=None, text="", html="", attrs=None, on_fill=None):
        if elements is not None:
            self.elements = elements
        else:
            self.elements = [self]
            self.text = text
            self.html = html
            self.attrs = attrs or {}
        self._on_fill = on_fill

    def filter(self, **kwargs):
        return self

    def count(self):
        return len(self.elements)

    def nth(self, i):
        if i < len(self.elements):
            return MockLocator([self.elements[i]], on_fill=self._on_fill)
        return MockLocator([])

    def all(self):
        return [MockLocator([e], on_fill=self._on_fill) for e in self.elements]

    @property
    def first(self):
        on_fill = self._on_fill or (self.elements[0]._on_fill if self.elements and hasattr(self.elements[0], '_on_fill') else None)
        return MockLocator([self.elements[0]], on_fill=on_fill) if self.elements else MockLocator([])

    def is_visible(self):
        return len(self.elements) > 0

    def click(self, **kwargs):
        pass

    def fill(self, text, **kwargs):
        if self.elements and self.elements[0] is not self:
            return self.elements[0].fill(text, **kwargs)
        if self._on_fill:
            self._on_fill(text)

    def press(self, key, **kwargs):
        pass

    def get_attribute(self, attr, **kwargs):
        if self.elements and self.elements[0] is not self:
            return self.elements[0].get_attribute(attr, **kwargs)
        return self.attrs.get(attr)

    def inner_text(self):
        if self.elements and self.elements[0] is not self:
            return self.elements[0].inner_text()
        return self.text

    def inner_html(self, **kwargs):
        if self.elements and self.elements[0] is not self:
            return self.elements[0].inner_html(**kwargs)
        return self.html

    def scroll_into_view_if_needed(self, **kwargs):
        pass

    def evaluate(self, script, **kwargs):
        pass

    def locator(self, selector):
        if self.elements and self.elements[0] is not self:
            return self.elements[0].locator(selector)

        if "xpath=parent" in selector:
            return MockLocator([MockLocator(text="Mocked job description")])
        if "img" in selector:
            return MockLocator([])
        return MockLocator([MockLocator(on_fill=self._on_fill)], on_fill=self._on_fill)


class MockPageE2E:
    def __init__(self):
        self.url = "https://www.linkedin.com/jobs/search/"

        class Mouse:
            def wheel(self, delta_x, delta_y):
                pass

        self.mouse = Mouse()

    def goto(self, url, **kwargs):
        self.url = url

    def wait_for_timeout(self, timeout):
        pass

    def evaluate(self, script, **kwargs):
        pass

    def content(self):
        return ""

    def locator(self, selector):
        if (
            "base-search-card" in selector
            or "job-card-container" in selector
            or "job-search-card" in selector
        ):
            return MockLocator(
                [
                    MockLocator(
                        html="<div class='title'>Software Engineer</div><div class='subtitle'>Acme Corp</div><a href='/company/acme'>Acme Corp</a>",
                        text="Software Engineer\\nAcme Corp",
                        attrs={
                            "data-entity-urn": "urn:li:jobPosting:123456789",
                            "href": "/jobs/view/123",
                        },
                    )
                ]
            )
        if "a[href*='/jobs/view/'] h2" in selector:
            return MockLocator([MockLocator(text="Software Engineer")])
        if "h1" in selector or "h2.t-24" in selector:
            return MockLocator([MockLocator(text="Software Engineer")])
        if 'a[href*="/company/"]' in selector:
            return MockLocator(
                [MockLocator(text="Acme Corp", attrs={"href": "/company/acme/"})]
            )
        if "About the job" in selector or "About the role" in selector:
            return MockLocator([MockLocator(text="About the job")])
        if "#job-details" in selector or ".jobs-description" in selector:
            return MockLocator([MockLocator(html="<p>Job description details...</p>")])

        if "input" in selector and "Search employees" in selector:
            return MockLocator([MockLocator(text="")])
        if "a[href*='/in/']" in selector:
            locators = []
            for i in range(1, 10):
                locators.append(
                    MockLocator(
                        text=f"Person {i}",
                        attrs={"href": f"https://linkedin.com/in/person{i}"},
                    )
                )
            return MockLocator(locators)

        if "Connect" in selector or "Invite" in selector:
            return MockLocator([MockLocator()])
        if "Add a note" in selector or "Add note" in selector:
            return MockLocator([MockLocator()])
        if "Send" in selector:
            return MockLocator([MockLocator()])
        if "textarea" in selector:
            return MockLocator([MockLocator()])

        return MockLocator([])


class MockContext:
    @property
    def pages(self):
        return []

    def new_page(self, **kwargs):
        return MockPageE2E()

    def close(self):
        pass


class MockBrowser:
    def new_page(self, **kwargs):
        return MockPageE2E()

    def close(self):
        pass


class Chromium:
    def launch(self, **kwargs):
        return MockBrowser()

    def launch_persistent_context(self, **kwargs):
        return MockContext()


class MockPlaywright:
    @property
    def chromium(self):
        return Chromium()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_extract_first_name_helper():
    from messenger import extract_first_name

    assert extract_first_name("Dr. Jane Doe") == "Jane"
    assert extract_first_name("Mr. John Smith") == "John"
    assert extract_first_name("Prof. Alan Turing") == "Alan"
    assert extract_first_name("Alice Johnson") == "Alice"
    assert extract_first_name("Bob") == "Bob"
    assert extract_first_name("View Alice") == "Alice"
    assert extract_first_name("View") == "there"
    assert extract_first_name("") == "there"


def test_real_time_pipeline_9_people():
    import importlib

    # Reload database to undo the mock
    import database
    import main
    import messenger

    importlib.reload(database)
    importlib.reload(messenger)

    print("Running Real-Time E2E Pipeline for 9 people...")

    config.MAX_MESSAGES_PER_DAY = 9
    config.MAX_PEOPLE_PER_COMPANY = 9
    config.MAX_COMPANIES_TO_PROCESS = 10
    config.DRY_RUN = False

    # Use test database
    import database

    database.DB_NAME = "test_linkedin_agent.db"
    if os.path.exists(database.DB_NAME):
        os.remove(database.DB_NAME)

    original_exists = os.path.exists

    def mock_exists(path):
        if path == main.SESSION_DIR:
            return True
        return original_exists(path)

    with (
        patch("main.sync_playwright", return_value=MockPlaywright()),
        patch("os.path.exists", side_effect=mock_exists),
    ):
        main.main()

    # verify
    conn = database.sqlite3.connect(database.DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM messaged_users")
    count = c.fetchone()[0]
    print(f"MESSAGED USERS: {count}")
    assert count == 9, f"Expected 9 users messaged, got {count}"

    if os.path.exists(database.DB_NAME):
        os.remove(database.DB_NAME)


def test_consecutive_outreach_targeting_isolation():
    from messenger import send_connection_request
    import database
    database.init_db()

    sent_messages = []

    class MockSequentialPage:
        def __init__(self):
            self.current_url = ""

        def goto(self, url, **kwargs):
            self.current_url = url

        def wait_for_timeout(self, timeout):
            pass

        def evaluate(self, script, **kwargs):
            pass

        def locator(self, selector):
            if "h1" in selector:
                if "alice" in self.current_url:
                    return MockLocator(text="Alice Smith")
                elif "bob" in self.current_url:
                    return MockLocator(text="Bob Jones")
                return MockLocator(text="Candidate")
            if "textarea" in selector:
                return MockLocator([MockLocator(on_fill=sent_messages.append)], on_fill=sent_messages.append)
            if "Connect" in selector or "Invite" in selector or "Add a note" in selector or "Send" in selector or "dialog" in selector or "modal" in selector:
                return MockLocator([MockLocator(on_fill=sent_messages.append)], on_fill=sent_messages.append)
            return MockLocator([MockLocator()])

    page = MockSequentialPage()
    job = {"title": "Software Engineer", "company": "Acme Corp", "job_id": "100"}
    config.DRY_RUN = False
    config.USER_INTRODUCTION = "I am a backend specialist."

    emp1 = {"name": "Alice Smith", "profile_url": "https://linkedin.com/in/alice", "company": "Acme Corp"}
    emp2 = {"name": "Bob Jones", "profile_url": "https://linkedin.com/in/bob", "company": "Acme Corp"}

    send_connection_request(page, emp1, job, "pitch1", config)
    send_connection_request(page, emp2, job, "pitch2", config)

    assert len(sent_messages) == 2
    assert "Hi Alice" in sent_messages[0]
    assert "Hi Bob" not in sent_messages[0]
    assert "Hi Bob" in sent_messages[1]
    assert "Hi Alice" not in sent_messages[1]



if __name__ == "__main__":
    test_user_introduction_env()
    test_real_time_pipeline_9_people()
