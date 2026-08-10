import config
from messenger import send_connection_request
import database
import messenger

def mock_log_user_messaged(url, name, company, job_id):
    pass
    
messenger.log_user_messaged = mock_log_user_messaged

def test_empty_introduction():
    class MockPage:
        pass

    employee = {"name": "Jane Smith", "profile_url": "https://linkedin.com/in/janesmith", "company": "Tech Inc"}
    job = {"title": "Data Scientist", "company": "Tech Inc", "job_id": "456"}
    ai_pitch = "I know SQL."

    config.USER_INTRODUCTION = ""
    config.DRY_RUN = True

    import sys
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    send_connection_request(MockPage(), employee, job, ai_pitch, config)

    sys.stdout = old_stdout
    output = mystdout.getvalue()
    
    print("OUTPUT:")
    print(output)
    
    assert "I'd be a great fit because I know SQL." in output

    print("Test passed!")

if __name__ == "__main__":
    test_empty_introduction()
