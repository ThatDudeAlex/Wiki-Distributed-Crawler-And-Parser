import logging
import os
import gzip
from typing import Tuple
from shared.utils import create_hash


def download_compressed_html_content(
    download_path: str, url: str, html_content: str, logger: logging.Logger
) -> Tuple[str, str]:
    """
    Compress and store HTML content to disk using a hash-based filename.

    Args:
        download_path (str): Directory where the file should be saved.
        url (str): URL that the content was fetched from.
        html_content (str): Raw HTML content to be saved.
        logger (logging.Logger): Logger instance for status output.

    Returns:
        Tuple[str, str]: (hash of URL, full path to the saved .gz file)

    Raises:
        OSError: If file cannot be written to disk
    """

    url_hash = create_hash(url)
    filename = f"{url_hash}.html.gz"
    filepath = os.path.join(download_path, filename)
    
    try:
        with gzip.open(filepath, "wt", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(
            f"Downloaded compressed HTML file for URL: {url} - filepath: {filepath}"
        )
        return url_hash, filepath

    except OSError as e:
        logger.error(
            f"Failed to write HTML file for URL: {url} | Path: {filepath} | Error: {e}"
        )
        raise
