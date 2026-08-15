import io
import sys
from unittest.mock import patch

import pytest

import config
from main import main


@patch("main.get_total_jobs_in_db")
@patch("main.log_job_processed")
@patch("main.init_db")
@patch("main.search_employees")
@patch("main.send_connection_request")
@patch("main.load_job_search_page")
@patch("main.extract_job_from_card")
@patch("main.sync_playwright")
@patch("os.path.exists")
def test_global_company_limit(
    mock_exists,
    mock_playwright,
    mock_extract,
    mock_load_page,
    mock_send,
    mock_search,
    mock_init,
    mock_log,
    mock_get_total,
):
    mock_exists.return_value = True
    config.MAX_PEOPLE_PER_COMPANY = 2
    config.MAX_MESSAGES_PER_DAY = 100
    config.MAX_COMPANIES_TO_PROCESS = 10

    mock_load_page.side_effect = [(3, "div.card"), (0, "div.card")]

    mock_extract.side_effect = [
        {
            "job_id": "1",
            "title": "Software Engineer",
            "company": "Tech Corp",
            "company_url": "url",
        },
        {
            "job_id": "2",
            "title": "Senior Engineer",
            "company": "Tech Corp",
            "company_url": "url",
        },
        {
            "job_id": "3",
            "title": "Principal Engineer",
            "company": "Tech Corp",
            "company_url": "url",
        },
    ]

    mock_search.side_effect = [
        [{"name": "Alice"}],  # 1 for first job
        [{"name": "Bob"}, {"name": "Charlie"}],  # 2 for second job
        [{"name": "Dave"}],  # 1 for third job
    ]

    mock_send.return_value = True

    # Capture stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output

    main()

    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()
    print("STDOUT from main():")
    print(output)

    assert mock_send.call_count == 2
    called_names = [call.args[1]["name"] for call in mock_send.call_args_list]
    assert called_names == ["Alice", "Bob"]

    assert "Company limit (2) reached for Tech Corp. Skipping outreach." in output


if __name__ == "__main__":
    pytest.main(["-v", "test_company_message_limit_global.py"])
