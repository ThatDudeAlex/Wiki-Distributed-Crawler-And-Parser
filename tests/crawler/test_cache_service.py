import pytest
from unittest.mock import MagicMock, patch
from crawler.cache_service import CacheService
from shared.config import R_ENQUEUED, R_VISITED

TEST_URL = "http://some_url"


@pytest.fixture
def cache_service():
    with patch('crawler.cache_service.redis.Redis') as mock_redis:
        mock_logger = MagicMock()
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance

        service = CacheService(mock_logger)

        yield service, mock_redis_instance, mock_logger


# TODO: convert to parametrize test cases

def test_initiate_pass(cache_service):
    service, mock_redis_instance, mock_logger = cache_service

    assert service._logger == mock_logger
    assert service._redis == mock_redis_instance


def test_initiate_failure():
    with pytest.raises(ValueError):
        CacheService(None)


def test_add_to_enqueued_set_pass(cache_service):
    service, mock_redis, mock_logger = cache_service

    got = service.add_to_enqueued_set(TEST_URL)

    assert got is True
    mock_redis.sadd.assert_called_once_with(R_ENQUEUED, TEST_URL)
    mock_logger.info.assert_called_once_with(
        f"Added to enqueued set: {TEST_URL}")


def test_add_to_enqueued_set_failure(cache_service):
    service, mock_redis, mock_logger = cache_service
    got = service.add_to_enqueued_set(None)

    assert got is False
    mock_redis.sadd.assert_not_called()
    mock_logger.info.assert_not_called()


def test_add_to_visited_set_pass(cache_service):
    service, mock_redis, mock_logger = cache_service

    got = service.add_to_visited_set(TEST_URL)

    assert got is True
    mock_redis.sadd.assert_called_once_with(R_VISITED, TEST_URL)
    mock_logger.info.assert_called_once_with(
        f"Added to visited set: {TEST_URL}")


def test_add_to_visited_set_failure(cache_service):
    service, mock_redis, mock_logger = cache_service
    got = service.add_to_visited_set(None)

    assert got is False
    mock_redis.sadd.assert_not_called()
    mock_logger.info.assert_not_called()


def test_set_if_not_existing_pass(cache_service):
    service, mock_redis, mock_logger = cache_service
    mock_redis.set.return_value = True

    got = service.set_if_not_existing(TEST_URL)

    assert got is True
    mock_redis.set.assert_called_once_with(f"enqueued:{TEST_URL}", 1, nx=True)
    mock_logger.info.assert_called_once_with(
        f"Set initiating seed key for: {TEST_URL}")


def test_set_if_not_existing_failure(cache_service):
    service, mock_redis, mock_logger = cache_service
    mock_redis.set.return_value = False

    got = service.set_if_not_existing(TEST_URL)

    assert got is False
    mock_redis.set.assert_called_once_with(f"enqueued:{TEST_URL}", 1, nx=True)
    mock_logger.info.assert_not_called()


def test_is_queueable_pass(cache_service):
    service, mock_redis, _ = cache_service
    mock_redis.sismember.return_value = False

    got = service.is_queueable(TEST_URL)

    assert got is True
    mock_redis.sismember.call_count == 2


def test_is_queueable_failure(cache_service):
    service, mock_redis, _ = cache_service
    mock_redis.sismember.return_value = True

    got = service.is_queueable(TEST_URL)

    assert got is False
    mock_redis.sismember.call_count == 2
