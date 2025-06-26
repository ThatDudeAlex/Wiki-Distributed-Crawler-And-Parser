from unittest.mock import patch, MagicMock
from crawler.download_handler import DownloadHandler


@patch("crawler.download_handler.create_hash")
@patch("gzip.open")
def test_download_compressed_html_content(mock_gzip_open, mock_create_hash):
    html_content = "<html><body><p>Hello World!</p></body></html>"
    url = "http://test.com"
    url_hash = "somehash"
    download_path = "output"
    expected_filepath = f"{download_path}/{url_hash}.html.gz"

    mock_logger = MagicMock()
    mock_file = MagicMock()
    mock_create_hash.return_value = url_hash
    mock_gzip_open.return_value.__enter__.return_value = mock_file

    service = DownloadHandler(mock_logger)

    result_hash, result_path = service.download_compressed_html_content(
        download_path, url, html_content)

    assert result_hash == url_hash
    assert result_path == expected_filepath
    mock_gzip_open.assert_called_once_with(
        expected_filepath, "wt", encoding="utf-8")
    mock_file.write.assert_called_once_with(html_content)
    mock_logger.info.assert_called_once()
