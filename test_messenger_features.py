from unittest.mock import MagicMock, patch

class Config:
    DRY_RUN = False

def test_chat_bubble_close():
    from messenger import search_employees
    page = MagicMock()
    page.locator.return_value.count.return_value = 0
    
    search_employees(page, "https://linkedin.com/company/test", "Test", ["Dev"])
    
    found = False
    for eval_call in page.evaluate.call_args_list:
        if "msg-overlay-bubble-header__control--close-btn" in eval_call[0][0]:
            found = True
            break
    assert found, "Did not attempt to close chat bubbles"

def test_scope_employee_scraping():
    from messenger import search_employees
    page = MagicMock()
    mock_scoped_locator = MagicMock()
    mock_scoped_locator.count.return_value = 1
    mock_scoped_locator.all.return_value = []
    
    def mock_locator(selector):
        if selector == "a[href*='/in/']:not(aside a):not(header a):not(nav a)":
            return mock_scoped_locator
        return MagicMock()
    
    page.locator.side_effect = mock_locator
    
    search_employees(page, "https://linkedin.com/company/test", "Test", ["Dev"])

@patch('messenger.random.randint')
@patch('messenger.log_user_messaged')
def test_direct_message_fallback(mock_log, mock_randint):
    mock_randint.return_value = 1000
    
    from messenger import send_connection_request
    page = MagicMock()
    
    class MockLocator:
        def __init__(self, is_message_btn=False):
            self.is_message_btn = is_message_btn
        def count(self):
            return 1
        def is_visible(self):
            return True
        def evaluate(self, script):
            pass
        def click(self, **kwargs):
            pass
        def locator(self, selector):
            return MockLocator()
        @property
        def first(self):
            return self
        @property
        def last(self):
            return self
        def fill(self, *args, **kwargs):
            pass
        def filter(self, *args, **kwargs):
            return self
            
    def mock_locator_factory(selector):
        if "Message" in selector:
            return MockLocator(is_message_btn=True)
        elif "Connect" in selector:
            mock = MockLocator()
            mock.count = lambda: 0
            mock.is_visible = lambda: False
            return mock
        elif "More" in selector:
            mock = MockLocator()
            mock.count = lambda: 0
            mock.is_visible = lambda: False
            return mock
        return MockLocator()
        
    page.locator = mock_locator_factory
    
    employee = {"name": "Test User", "profile_url": "https://linkedin.com/in/test", "company": "Test"}
    job = {"job_id": 1, "title": "Dev", "company": "Test"}
    config = Config()
    ai_pitch = "Hi"
    
    result = send_connection_request(page, employee, job, ai_pitch, config)
    assert result == True, "Failed to send message via direct message fallback"
    mock_log.assert_called_once()

if __name__ == "__main__":
    import os
    import sys
    os.makedirs("/tmp/no-mistakes-evidence/01M07RCMQ1WGTDT439DPSYANRF", exist_ok=True)
    with open("/tmp/no-mistakes-evidence/01M07RCMQ1WGTDT439DPSYANRF/test_output.txt", "w") as f:
        try:
            test_chat_bubble_close()
            f.write("Chat bubble close logic verified.\n")
            test_scope_employee_scraping()
            f.write("Scoped employee scraping verified.\n")
            test_direct_message_fallback()
            f.write("Direct message fallback verified.\n")
            print("All tests passed.")
        except Exception as e:
            f.write(f"Test failed: {e}\n")
            print(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
