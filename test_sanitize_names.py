from unittest.mock import MagicMock, patch

from messenger import search_employees


@patch("messenger.is_user_messaged", return_value=False)
def test_employee_sanitize(mock_is_user_messaged):
    page = MagicMock()

    # Mocking locators for profile links
    class MockLocator:
        def __init__(self, href, inner_text="", alt_text=""):
            self.href = href
            self._inner_text = inner_text
            self.alt_text = alt_text

        def get_attribute(self, attr):
            if attr == "href":
                return self.href
            elif attr == "alt":
                return self.alt_text
            return None

        def inner_text(self):
            return self._inner_text

        def locator(self, selector):
            mock_img = MagicMock()
            if self.alt_text:
                mock_img.first.count.return_value = 1
                mock_img.first.get_attribute.return_value = self.alt_text
            else:
                mock_img.first.count.return_value = 0
            return mock_img

    def mock_all():
        return [
            # Name with 'open to work'
            MockLocator(href="/in/johndoe", inner_text="John Doe \n is open to work"),
            MockLocator(href="in/janedoe", inner_text="Jane Doe\n follows this page"),
            MockLocator(
                href="/in/bobsmith?someParam=value", inner_text="Bob Smith works here"
            ),
            MockLocator(
                href="https://www.linkedin.com/in/alice",
                inner_text="Alice   is open to work ",
            ),
            MockLocator(
                href="https://www.linkedin.com/in/charlie",
                inner_text="Charlie\nView Charlie's profile",
            ),
            MockLocator(
                href="/in/imageonly",
                inner_text="",
                alt_text="ImageOnly is open to work",
            ),
            MockLocator(
                href="/in/maryjane",
                inner_text="Mary   Jane",
            ),
            MockLocator(
                href="/in/viewonly",
                inner_text="View ViewOnly",
            ),
            MockLocator(
                href="/in/viewprofile",
                inner_text="View ViewProfile's profile",
            ),
        ]

    mock_links_locator = MagicMock()
    mock_links_locator.all = mock_all

    # Mocking page methods
    def page_locator(selector):
        if selector == "a[href*='/in/']":
            return mock_links_locator

        # search input mock
        search_input = MagicMock()
        search_input.first.count.return_value = 0
        return search_input

    page.locator = page_locator

    # Bypass navigation delays
    page.goto = MagicMock()
    page.wait_for_timeout = MagicMock()
    page.evaluate = MagicMock()

    employees = search_employees(
        page, "https://linkedin.com/company/test", "Test Company", ["Developer"]
    )

    # Print results for verification
    for emp in employees:
        print(f"Name: '{emp['name']}', URL: '{emp['profile_url']}'")

    # Assertions
    assert len(employees) == 9
    assert employees[0]["name"] == "John Doe"
    assert employees[0]["profile_url"] == "https://www.linkedin.com/in/johndoe"

    assert employees[1]["name"] == "Jane Doe"
    assert employees[1]["profile_url"] == "https://www.linkedin.com/in/janedoe"

    assert employees[2]["name"] == "Bob Smith"
    assert employees[2]["profile_url"] == "https://www.linkedin.com/in/bobsmith"

    assert employees[3]["name"] == "Alice"
    assert employees[3]["profile_url"] == "https://www.linkedin.com/in/alice"

    assert employees[4]["name"] == "Charlie"
    assert employees[4]["profile_url"] == "https://www.linkedin.com/in/charlie"

    assert employees[5]["name"] == "ImageOnly"
    assert employees[5]["profile_url"] == "https://www.linkedin.com/in/imageonly"

    assert employees[6]["name"] == "Mary Jane"
    assert employees[6]["profile_url"] == "https://www.linkedin.com/in/maryjane"

    assert employees[7]["name"] == "ViewOnly"
    assert employees[7]["profile_url"] == "https://www.linkedin.com/in/viewonly"

    assert employees[8]["name"] == "ViewProfile"
    assert employees[8]["profile_url"] == "https://www.linkedin.com/in/viewprofile"

    print("All assertions passed!")


if __name__ == "__main__":
    test_employee_sanitize()
