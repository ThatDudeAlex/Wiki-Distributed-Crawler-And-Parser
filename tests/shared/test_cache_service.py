import pytest
from unittest.mock import MagicMock, patch
from shared.redis.cache_service import CacheService

# TODO: Update test cases


@pytest.fixture
def mock_redis():
    with patch("shared.cache_service.redis.Redis") as mock_redis_class:
        mock_redis_instance = MagicMock()
        mock_redis_class.return_value = mock_redis_instance
        yield mock_redis_instance


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def cache_service(mock_logger, mock_redis):
    return CacheService(logger=mock_logger)


# def test_add_to_enqueued_set(cache_service, mock_redis, mock_logger):
#     assert cache_service.add_to_enqueued_set("http://test.com") is True
#     mock_redis.sadd.assert_called_with(
#         RedisSets.SEEN.value, "http://test.com")
#     mock_logger.info.assert_called()


# def test_add_to_enqueued_set_none(cache_service):
#     assert cache_service.add_to_enqueued_set(None) is False


# def test_set_if_not_existing(cache_service, mock_redis, mock_logger):
#     mock_redis.set.return_value = True
#     assert cache_service.set_if_not_existing("http://test.com") is True
#     mock_redis.set.assert_called_with("enqueued:http://test.com", 1, nx=True)
#     mock_logger.info.assert_called()


# def test_set_if_not_existing_already_exists(cache_service, mock_redis):
#     mock_redis.set.return_value = False
#     assert cache_service.set_if_not_existing("http://test.com") is False


# @pytest.mark.parametrize(
#     "is_in_visited_return, is_in_enqueued_return, expected_queueable",
#     [
#         (True, False, True),   # In visited, not in enqueued -> True
#         (False, True, True),   # Not in visited, in enqueued -> True
#         (True, True, True),    # In both -> True
#         (False, False, False)  # Not in either -> False
#     ]
# )
# def test_is_queueable(
#     cache_service, is_in_visited_return, is_in_enqueued_return, expected_queueable
# ):
#     cache_service.is_in_visited = MagicMock(return_value=is_in_visited_return)
#     cache_service.is_in_enqueued = MagicMock(
#         return_value=is_in_enqueued_return)
#     assert cache_service.is_queueable("http://test.com") is expected_queueable


# def test_cache_service_init_no_logger_raises_error(mock_redis):
#     with pytest.raises(ValueError, match="logger is required"):
#         CacheService(logger=None)
