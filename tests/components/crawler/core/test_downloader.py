import os
import gzip
import pytest
from unittest.mock import MagicMock, patch
from components.crawler.core.downloader import download_compressed_html_content

# tmp_path is a built-in pytest fixture
def test_download_compressed_html_success(tmp_path):
    # Setup
    download_path = str(tmp_path)
    url = "http://example.com"
    html_content = "<html>Test</html>"
    logger = MagicMock()

    # Act
    url_hash, filepath = download_compressed_html_content(download_path, url, html_content, logger)

    # Assert
    assert os.path.exists(filepath)

    with gzip.open(filepath, "rt", encoding="utf-8") as f:
        saved_content = f.read()
        assert saved_content == html_content

    assert url_hash in os.path.basename(filepath)


# tmp_path is a built-in pytest fixture
def test_download_compressed_html_raises_oserror(tmp_path):
    # Setup
    download_path = str(tmp_path)
    url = "http://example.com"
    html_content = "<html>Test</html>"
    logger = MagicMock()

    # Act & Assert
    with patch("components.crawler.core.downloader.gzip.open", side_effect=OSError("disk error")):
        with pytest.raises(OSError, match="disk error"):
            download_compressed_html_content(download_path, url, html_content, logger)
