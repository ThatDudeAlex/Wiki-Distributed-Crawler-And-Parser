import logging
import os
import gzip
from bs4 import BeautifulSoup, Comment
from typing import Tuple
from shared.utils import create_hash


class DownloadHandler:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def clean_html_content(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, "lxml")

        # Remove <script>, <style>, <noscript>, etc...
        for tag in soup(["script", "style", "noscript", "iframe", "footer", "sup"]):
            tag.decompose()

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Remove potential ads or tracking elements
        for tag in soup.select("[class*='ad'], [id*='ad'], [class*='tracking'], [id*='tracking']"):
            tag.decompose()

        return str(soup)

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
        cleaned_html = self.clean_html_content(html_content)

        with gzip.open(filepath, "wt", encoding="utf-8") as f:
            f.write(cleaned_html)

        self._logger.info(
            f"Downloaded compressed HTML for URL: {url} - filepath: {filepath}")
        return (url_hash, filepath)
