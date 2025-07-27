from unittest.mock import Mock
import pytest
from components.scheduler.core.filter import FilteringService
from shared.rabbitmq.schemas.scheduling import LinkData


TEST_SOURCE_URL='https://en.wikipedia.org'
TEST_URL="https://en.wikipedia.org/wiki/Python"
TEST_DISCOVERED_AT="2025-07-25T00:00:00Z"


@pytest.fixture
def filtering_service():
    configs = {
        "filters": {
            "max_depth": 2,
            "allowed_domains": ["en.wikipedia.org"],
            "excluded_prefixes": ["/wiki/File:", "/wiki/Special:"],
            "robots_txt": "https://en.wikipedia.org/robots.txt",
        },
        "http_headers": {
            "user-agent": "MyCrawlerBot"
        }
    }
    logger = Mock()
    return FilteringService(configs, logger)


@pytest.fixture
def mock_linkdata():
    return LinkData(
        source_page_url=TEST_SOURCE_URL,
        url=TEST_URL, 
        depth=2,
        discovered_at=TEST_DISCOVERED_AT
    )


def test_exceeds_max_depth_true(filtering_service, mock_linkdata):
    # Depth is above the max_depth (2)
    mock_linkdata.depth = 3
    assert filtering_service._exceeds_max_depth(mock_linkdata) is True


def test_exceeds_max_depth_false(filtering_service, mock_linkdata):
    # Depth is equal to max_depth
    assert filtering_service._exceeds_max_depth(mock_linkdata) is False

    # Depth is below max_depth
    mock_linkdata.depth = 1
    assert filtering_service._exceeds_max_depth(mock_linkdata) is False


def test_is_external_domain_true(filtering_service, mock_linkdata):
    # URL is from a disallowed domain
    mock_linkdata.url="https://example.com/some-page"
    assert filtering_service._is_external_domain(mock_linkdata) is True


def test_is_external_domain_false(filtering_service, mock_linkdata):
    # URL is from an allowed domain
    assert filtering_service._is_external_domain(mock_linkdata) is False


def test_is_blocked_by_robot_true(filtering_service, mock_linkdata):
    filtering_service._robots_parser = Mock()
    filtering_service._robots_parser.can_fetch.return_value = False

    assert filtering_service._is_blocked_by_robot(mock_linkdata) is True
    filtering_service._robots_parser.can_fetch.assert_called_once()


def test_is_blocked_by_robot_false(filtering_service, mock_linkdata):
    filtering_service._robots_parser = Mock()
    filtering_service._robots_parser.can_fetch.return_value = True

    assert filtering_service._is_blocked_by_robot(mock_linkdata) is False
    filtering_service._robots_parser.can_fetch.assert_called_once()


def test_is_not_article_page_due_to_excluded_prefix(filtering_service, mock_linkdata):
    mock_linkdata.url="https://en.wikipedia.org/wiki/File:Example.jpg"
    assert filtering_service._is_not_article_page(mock_linkdata) is True


def test_is_not_article_page_due_to_homepage(filtering_service, mock_linkdata):
    mock_linkdata.url="https://en.wikipedia.org/"
    assert filtering_service._is_not_article_page(mock_linkdata) is True


def test_is_not_article_page_false_for_valid_article(filtering_service, mock_linkdata):
    assert filtering_service._is_not_article_page(mock_linkdata) is False
