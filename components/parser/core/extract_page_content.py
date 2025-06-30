
import logging

from bs4 import BeautifulSoup, Tag
from components.parser.core.html_content_cleaner import clean_content
from shared.utils import create_hash


def extract_page_content(html_content: str, logger: logging.Logger):
    soup = BeautifulSoup(html_content, "lxml")

    # Step 1 - extract <title>
    title = _extract_title(soup, logger)

    # TODO: Implement this in the fututure after updating table schema
    # Step (2) - Extract content from <meta> tags (examples: description, robots, charset)
    # meta_tags = _extract_meta_tags(soup, logger)

    # Step 2 - Extract Page Categories
    categories = _extract_categories(soup, logger)

    # Step 4 - Get Main Content Area
    main_content = _extract_main_body_content(soup, logger)

    summary, text_content, text_content_hash = None

    if not main_content:
        logger.warning(
            'Failed To Find Main Content - Skipping Summary & Text_Content')

    if main_content:
        # Step 5 - Extract Page Summary (First Non-Empty Paragraph from Main Content)
        summary = _extract_summary(soup, main_content, logger)

        # Step 6 - Clean Text Content (Boilerplate Removal)
        clean_main_content = clean_content(main_content, logger)

        # Step 7 - Extract Clean Main Text
        text_content = clean_main_content.get_text()

        # Step 8 - Hash Text Content
        text_content_hash = create_hash(text_content)

    page_content = {
        title: title,
        categories: categories,
        summary: summary,
        text_content: text_content,
        text_content_hash: text_content_hash
    }

    return page_content


def _extract_title(soup: BeautifulSoup, logger: logging.Logger):
    try:
        title_tag = soup.find('title')

        if title_tag:
            title = title_tag.get_text(strip=True)
            logger.info('Title Extracted: %s', title)
            return title

        logger.warning('Missing Page Title')
        return None
    except Exception as e:
        exception_type_name = type(e).__name__
        logger.error(
            f"An exception of type '{exception_type_name}' occurred: {e}")
        return None


def _extract_main_body_content(soup: BeautifulSoup, logger: logging.Logger):
    try:
        return soup.find('div', id='#mw-content-text')
    except Exception as e:
        exception_type_name = type(e).__name__
        logger.error(
            f"An exception of type '{exception_type_name}' occurred: {e}")
        return None


def _extract_categories(soup: BeautifulSoup, logger: logging.Logger):
    try:
        categories = []
        normal_catlinks_div = soup.find('div', id='mw-normal-catlinks')

        if normal_catlinks_div:
            # Find all anchor tags (<a>) within this div
            category_links = normal_catlinks_div.find_all('a')

            for link in category_links:
                # The category name is usually the text content of the link
                # We also want to remove any potential "Category:" prefix
                # that's in the text content
                category_text = link.get_text(strip=True)

                if category_text.startswith("Category:"):
                    categories.append(category_text[len("Category:"):])
                else:
                    categories.append(category_text)

        if categories:
            logger.info('Categories Extracted: %s', categories)
        else:
            logger.warning('Missing Page Categories')

        return categories
    except Exception as e:
        exception_type_name = type(e).__name__
        logger.error(
            f"An exception of type '{exception_type_name}' occurred: {e}")
        return []


def _extract_summary(main_content: Tag, logger: logging.Logger):
    try:
        # Find all anchor tags (<a>) within this div
        paragraphs = main_content.find_all('p', recursive=False)

        for p in paragraphs:
            # strip whitespaces
            paragraph_text = p.get_text(strip=True)

            if paragraph_text:
                # Filter out common "non-summary" elements that might appear as first paragraphs
                # such as disambiguation notes, coordination notices, etc.
                # This list might need to be expanded based on edge cases I find.
                if not (
                    paragraph_text.startswith("Coordinates:") or
                    paragraph_text.startswith("For other uses, see") or
                    paragraph_text.startswith("This article is about") or
                    paragraph_text.startswith("This is a redirect") or
                    paragraph_text.lower().startswith("disambiguation")
                ):
                    logger.info('Summary Extracted: %s', paragraph_text)
                    return paragraph_text

        logger.warning('Missing Page Summary')
        return None
    except Exception as e:
        exception_type_name = type(e).__name__
        logger.error(
            f"An exception of type '{exception_type_name}' occurred: {e}")
        return None
