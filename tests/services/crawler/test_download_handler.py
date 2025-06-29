import os
import tempfile

from unittest.mock import patch, MagicMock
from components.crawler.config import CRAWLER_SEED_URL
from components.crawler.infrastructure.download_handler import download_compressed_html_content


def test_download_compressed_html_content_with_real_html():
    # Setup
    test_url = CRAWLER_SEED_URL
    html_file_path = "tests/data/sample_wikipedia_page.html"

    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Use temp directory for the download
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock hash and logger
        with patch("services.crawler.infrastructure.download_handler.create_hash",
                   return_value="dummyhash123") as mock_hash:
            mock_logger = MagicMock()

            # Act
            url_hash, filepath = download_compressed_html_content(
                tmpdir, test_url, html_content, mock_logger)

            # Assert
            assert url_hash == "dummyhash123"
            assert os.path.exists(filepath)
            assert filepath.endswith(".html.gz")
