import pytest
from unittest.mock import MagicMock, patch

from requests import RequestException
from components.dispatcher.services.db_client import DBReaderClient


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def client(mock_logger):
    return DBReaderClient(
        logger=mock_logger,
        db_timeout=5,
        host="http://fake-db-reader"
    )


@patch("components.dispatcher.services.db_client.requests.Session.get")
def test_pop_links_success(mock_get, client):
    # Setup
    mock_response = MagicMock()
    mock_response.json.return_value = [{"url": "https://a.com", "depth": 1, "scheduled_at": "2025-07-25T00:00:00Z"}]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Act
    result = client.pop_links_from_schedule(5)

    # Assert
    mock_get.assert_called_once_with(
        "http://fake-db-reader/get_scheduled_links",
        params={"count": 5},
        timeout=5
    )
    assert result == mock_response.json.return_value


@patch("components.dispatcher.services.db_client.requests.Session.get")
def test_pop_links_failure_logs_exception(mock_get, client, mock_logger):
    # Setup
    mock_get.side_effect = RequestException("error")

    # Act
    result = client.pop_links_from_schedule(3)

    # Assert
    assert result is None


@patch("components.dispatcher.services.db_client.requests.Session.get")
def test_tables_are_empty_success(mock_get, client):
    mock_response = MagicMock()
    mock_response.json.return_value = True
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = client.tables_are_empty()

    mock_get.assert_called_once_with(
        "http://fake-db-reader/tables/empty",
        timeout=5
    )
    assert result is True


@patch("components.dispatcher.services.db_client.requests.Session.get")
def test_tables_are_empty_failure_logs_exception(mock_get, client):
    # Setup
    mock_get.side_effect = RequestException("fail")

    # Act
    result = client.tables_are_empty()

    # Assert
    assert result is None