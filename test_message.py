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


def test_message_10_people():
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

    import messenger
    messaged = []
    messenger.log_user_messaged = lambda url, name, company, job_id: messaged.append((name, url))

    config.DRY_RUN = True
    job = {"title": "AI Engineer", "company": "TechCorp", "job_id": "456"}

    for i in range(10):
        employee = {
            "name": f"Candidate {i+1}",
            "profile_url": f"https://linkedin.com/in/candidate{i+1}",
            "company": "TechCorp",
        }
        success = send_connection_request(MockPage(), employee, job, "Great fit", config)
        assert success is True

    assert len(messaged) == 10
    print(f"Successfully messaged {len(messaged)} people in test pipeline!")


if __name__ == "__main__":
    test_user_introduction_env()
    test_message_10_people()
