import logging
import re
from bs4 import BeautifulSoup, Comment, Tag
from components.parser.configs.app_configs import WIKIPEDIA_BOILERPLATE_SELECTORS


def clean_content(main_content: Tag, logger: logging.Logger) -> Tag:
    try:

        if main_content is None:
            logger.warning("None is an invalid main_content type")
            return main_content

        # main_content is passed by referrence, so create a copy of the main_content to
        # modify it without affecting the original soup. Idk if I might need the original
        # soup for other extractions later
        cleaned_content = BeautifulSoup(str(main_content), "lxml")

        # --- 1. Remove known Wikipedia-specific boilerplate elements within the main content ---
        # These elements are consistently used by Wikipedia and are NOT core article text.

        # Remove script, style tags, and comments first from the whole soup or main_content
        for script_or_style in cleaned_content(["script", "style"]):
            script_or_style.decompose()
        for comment in cleaned_content.find_all(
            string=lambda text: isinstance(text, Comment)
        ):
            comment.extract()

        for selector in WIKIPEDIA_BOILERPLATE_SELECTORS:
            for element in main_content.select(selector):
                element.decompose()

        # --- 2. Extract text from the cleaned main content div ---
        clean_text = main_content.get_text(separator=" ", strip=True)

        # --- 3. Further text cleaning (e.g., multiple spaces, newlines) ---
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        logger.info('Cleaned Main Text Context')
        return clean_text
    except Exception as e:
        exception_type_name = type(e).__name__
        logger.error(
            f"An exception of type '{exception_type_name}' occurred: {e}")
        return None
