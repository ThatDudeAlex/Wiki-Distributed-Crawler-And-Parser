import gzip
import logging
from typing import Optional


def load_compressed_html(filepath: str, logger: logging.Logger) -> Optional[str]:
    """
    Loads and decompresses gzipped HTML content from the specified file path

    Args:
        filepath (str): Path to the .gz compressed HTML file
        logger (logging.Logger): Logger instance for logging events

    Returns:
        Optional[str]: Decompressed HTML content, or None if an error occurred
    """
    try:
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            html_content = f.read()

        logger.info(f"Loaded compressed HTML file from: {filepath}")
        return html_content
    except Exception:
        logger.exception(f"Failed to load compressed HTML from {filepath}")
        return None
