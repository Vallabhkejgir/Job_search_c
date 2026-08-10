from messenger import search_employees
from unittest.mock import MagicMock

class MockLocator:
    def __init__(self, href, inner_text="", alt_text=""):
        self._href = href
        self._inner_text = inner_text
        self._alt_text = alt_text

    def get_attribute(self, attr):
        if attr == "href":
            return self._href
        if attr == "alt":
            return self._alt_text
        return None

    def inner_text(self):
        return self._inner_text

    def locator(self, selector):
        mock_img = MagicMock()
        mock_img.count.return_value = 1 if self._alt_text else 0
        mock_img.get_attribute.side_effect = lambda a: self._alt_text if a == "alt" else None
        
        mock_loc = MagicMock()
        mock_loc.first = mock_img
        return mock_loc

page = MagicMock()
links = MagicMock()
links.all.return_value = [
    MockLocator(href="/in/maryjane", inner_text="", alt_text="Mary   Jane")
]
page.locator.return_value = links

employees = search_employees(page, "https://linkedin.com", "TestCo", ["Engineer"])
print("Result:")
for e in employees:
    print(repr(e['name']))
