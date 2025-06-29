import logging
import os
import gzip
from bs4 import BeautifulSoup, Comment
from typing import Tuple
from shared.utils import create_hash


def _clean_html_content(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "lxml")

    for tag in soup(["script", "style", "noscript", "iframe", "footer", "sup"]):
        tag.decompose()

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    cleaned_text = soup.get_text(separator=" ", strip=True)
    cleaned_text = ' '.join(cleaned_text.split())

    return str(soup)


def download_compressed_html_content(download_path: str, url: str, html_content: str, logger: logging.Logger) -> Tuple[str, str]:
    url_hash = create_hash(url)
    filename = f"{url_hash}.html.gz"
    filepath = os.path.join(download_path, filename)
    cleaned_html = _clean_html_content(html_content)

    with gzip.open(filepath, "wt", encoding="utf-8") as f:
        f.write(cleaned_html)

    logger.info(
        f"Downloaded compressed HTML file for URL: {url} - filepath: {filepath}")
    return (url_hash, filepath)
