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


def test_real_time_pipeline_9_people():
    import main
    print("Running Real-Time E2E Pipeline for 9 people...")

    # Override configuration for the test
    config.MAX_MESSAGES_PER_DAY = 9
    config.MAX_PEOPLE_PER_COMPANY = 9
    config.MAX_COMPANIES_TO_PROCESS = 10
    config.DRY_RUN = False

    # Run the full pipeline
    main.main()


if __name__ == "__main__":
    test_user_introduction_env()
    test_real_time_pipeline_9_people()
