import logging
import os
import gzip
from typing import Tuple
from shared.utils import create_hash


class DownloadHandler:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def download_compressed_html_content(self, download_path: str, url: str, html_content: str) -> Tuple[str, str]:
        """
        Downloads the ``HTML`` content into as a compressed file into the ``download_path``.
        The downloaded file will be named after a hash of its ``URL`` and follow this naming
        format: ``url_hash.html.gz``

        Returns the following Tuple: ``(url_hash, filepath)``
        """
        url_hash = create_hash(url)
        filename = f"{url_hash}.html.gz"
        filepath = os.path.join(download_path, filename)

        with gzip.open(filepath, "wt", encoding="utf-8") as f:
            f.write(html_content)

        self._logger.info(
            f"Downloaded compressed HTML for URL: {url} - filepath: {filepath}")
        return (url_hash, filepath)
