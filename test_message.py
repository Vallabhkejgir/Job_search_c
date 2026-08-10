import config
from messenger import send_connection_request
import database

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

    employee = {"name": "John Doe", "profile_url": "https://linkedin.com/in/johndoe", "company": "Acme Corp"}
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

if __name__ == "__main__":
    test_user_introduction_env()
