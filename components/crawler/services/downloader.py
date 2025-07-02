import logging
import os
import gzip
from typing import Tuple
from shared.utils import create_hash


def download_compressed_html_content(download_path: str, url: str, html_content: str, logger: logging.Logger) -> Tuple[str, str]:
    url_hash = create_hash(url)
    filename = f"{url_hash}.html.gz"
    filepath = os.path.join(download_path, filename)

    with gzip.open(filepath, "wt", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(
        f"Downloaded compressed HTML file for URL: {url} - filepath: {filepath}")
    return (url_hash, filepath)
