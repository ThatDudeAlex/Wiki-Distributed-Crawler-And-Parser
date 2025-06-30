import pytest
from unittest.mock import MagicMock, patch
from components.crawler.services.crawler_service import CrawlerService


@pytest.fixture
def mock_queue():
    return MagicMock()


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def crawler_service(mock_queue, mock_logger):
    return CrawlerService(queue_service=mock_queue, logger=mock_logger, max_depth=2)


@patch('components.crawler.services.crawler_service.crawl')
def test_run_skips_when_depth_exceeded(mock_crawl, crawler_service, mock_logger):
    crawler_service.run("http://example.com", depth=3)
    mock_crawl.assert_not_called()


# @patch('components.crawler.services.crawler_service.crawl')
# def test_run_failed_crawl_publishes_failed_task(mock_crawl, crawler_service, mock_queue):
#     mock_crawl.return_value = CrawlerResponse(
#         success=False,
#         url="http://example.com",
#         crawl_status=CrawlStatus.CRAWL_FAILED,
#         data=None,
#         error={'type': 'HTTPError', 'message': 'Request failed'}
#     )
#     crawler_service.run("http://example.com", depth=1)

#     assert mock_queue.publish.call_count == 1
#     args, kwargs = mock_queue.publish.call_args

#     assert args[1]['crawl_status'].value == CrawlStatus.CRAWL_FAILED.value
#     assert str(args[1]['url']) == "http://example.com/"
#     assert args[1]['error_message'] == 'Request failed'


# @patch('services.crawler.service.crawler_service.get_timestamp_eastern_time', return_value='mocked_time')
# @patch('services.crawler.service.crawler_service.download_compressed_html_content')
# @patch('components.crawler.services.crawler_service.crawl')
# def test_run_successful_crawl_publishes_all_tasks(mock_crawl, mock_download, mock_time, crawler_service, mock_queue):
#     mock_crawl.return_value = CrawlerResponse(
#         success=True,
#         url="http://example.com",
#         crawl_status=CrawlStatus.CRAWLED_SUCCESS,
#         data=ResponseData(status_code=200, headers={}, text="<html></html>"),
#         error=None
#     )
#     with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
#         mock_download.return_value = ("hash123", Path(tmp_file.name))

#         crawler_service.run("http://example.com", depth=1)

#         published_channels = [call_args[0][0]
#                               for call_args in mock_queue.publish.call_args_list]
#         assert set(published_channels) == {
#             'save_crawled_pages', 'parse_tasks'
#         }


# @patch('services.crawler.service.crawler_service.download_compressed_html_content', side_effect=Exception("Download failed"))
# @patch('components.crawler.services.crawler_service.crawl')
# def test_run_download_failure(mock_crawl, mock_download, crawler_service, mock_logger):
#     mock_crawl.return_value = CrawlerResponse(
#         success=True,
#         url="http://example.com",
#         crawl_status=CrawlStatus.CRAWLED_SUCCESS,
#         data=ResponseData(status_code=200, headers={}, text="<html></html>"),
#         error=None
#     )
#     with pytest.raises(Exception) as e:
#         crawler_service.run("http://example.com", depth=1)
#     assert str(e.value) == "Download failed"


# @patch('components.crawler.services.crawler_service.crawl')
# def test_run_handles_empty_url_gracefully(mock_crawl, crawler_service):
#     with pytest.raises(Exception):
#         crawler_service.run("", depth=1)


# @patch('components.crawler.services.crawler_service.crawl')
# def test_run_handles_none_url(mock_crawl, crawler_service):
#     with pytest.raises(Exception):
#         crawler_service.run(None, depth=1)


# @patch.dict(os.environ, {}, clear=True)
# @patch('components.crawler.services.crawler_service.crawl')
# def test_run_missing_env_path(mock_crawl, crawler_service):
#     mock_crawl.return_value = CrawlerResponse(
#         success=True,
#         url="http://example.com",
#         crawl_status=CrawlStatus.CRAWLED_SUCCESS,
#         data=ResponseData(status_code=200, headers={}, text="<html></html>"),
#         error=None
#     )
#     with pytest.raises(TypeError):
#         crawler_service.run("http://example.com", depth=1)
