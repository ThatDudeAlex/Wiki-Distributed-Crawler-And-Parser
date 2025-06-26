from unittest.mock import MagicMock, patch
from crawler.fetcher import Fetcher

# TODO: Expand the test cases and use parametrized test


@patch("crawler.fetcher.requests.Session.get")
def test_fetcher_get_success(mock_get):
    mock_logger = MagicMock()
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None  # no error
    mock_response.status_code = 200
    mock_response.text = "<html>Hello</html>"

    mock_get.return_value = mock_response

    fetcher = Fetcher(mock_logger)
    url = "https://someurl.com"

    response = fetcher.get(url)

    mock_get.assert_called_once_with(url)
    mock_response.raise_for_status.assert_called_once()
    assert response.text == "<html>Hello</html>"
    assert response.status_code == 200
