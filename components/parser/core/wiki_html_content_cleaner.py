import logging
import re
from bs4 import BeautifulSoup, Comment, Tag
from components.parser.configs.app_configs import WIKIPEDIA_BOILERPLATE_SELECTORS


def clean_wiki_html_content(main_content: Tag, logger: logging.Logger) -> str:
    """
    Cleans Wikipedia main content HTML by removing scripts, styles,
    boilerplate selectors, and unnecessary whitespace.
    """
    try:
        if main_content is None:
            logger.warning("clean_wiki_html_content received None")
            return ""

        # Clone the content to avoid mutating the original Tag
        cleaned_soup = BeautifulSoup(str(main_content), "lxml")

        # Remove <script>, <style> tags
        for tag in cleaned_soup(["script", "style"]):
            tag.decompose()

        # Remove comments
        for comment in cleaned_soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Remove Wikipedia boilerplate elements
        for selector in WIKIPEDIA_BOILERPLATE_SELECTORS:
            for element in cleaned_soup.select(selector):
                element.decompose()

        # Extract and normalize text
        clean_text = cleaned_soup.get_text(separator=" ", strip=True)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        logger.info(f"Cleaned main content (length: {len(clean_text)} chars)")
        return clean_text

    except Exception as e:
        logger.error(f"[clean_wiki_html_content] {type(e).__name__}: {e}")
        return ""
