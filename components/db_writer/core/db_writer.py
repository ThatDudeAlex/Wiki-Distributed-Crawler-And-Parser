from contextlib import contextmanager
import logging
from typing import List

from sqlalchemy.exc import DataError, IntegrityError, OperationalError
from sqlalchemy.orm import Session
from database.engine import SessionLocal
from database.db_models.models import Category, Page, PageContent, CrawlStatus
from components.db_writer.configs.app_configs import MAX_RETRIES


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


def save_crawled_page(page_data: dict, logger: logging.Logger) -> bool:
    """
    Inserts a new Page or updates crawl metadata if it already exists.

    If a Page with the same URL exists:
        - Updates last_crawled_at and crawl_attempts.
    Else:
        - Inserts a new Page.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with get_db() as db:

                # Try finding an existing page by URL
                existing = db.query(Page).filter_by(
                    url=page_data['url']).first()

                # If URL exist then just update metadata
                if existing:
                    existing.last_crawled_at = page_data['crawl_time']
                    existing.crawl_attempts = existing.crawl_attempts + 1

                    logger.debug(
                        f"Updated existing page: '{page_data['url']}' with new crawl metadata."
                    )
                    return True

                # No match on URL — insert new Page
                new_page = Page(
                    url=page_data['url'],
                    url_hash=page_data['url_hash'],
                    last_crawl_status=CrawlStatus.CRAWLED_SUCCESS,
                    http_status_code=page_data['status_code'],
                    compressed_path=page_data['compressed_path'],
                    last_crawled_at=page_data['crawl_time'],
                    crawl_attempts=1
                )
                db.add(new_page)

                logger.debug(
                    f"Inserted new page: '{page_data['url']}' into the database.")
                return True

        except (IntegrityError, DataError) as e:
            logger.warning(
                f"Non-recoverable DB error while saving page: {page_data['url']} - {e}")
            return False
        except OperationalError as e:
            logger.warning(
                f"OperationalError while saving page: {page_data['url']} - Attempt {attempt}/{MAX_RETRIES} - {e}")
        except Exception as e:
            logger.exception(
                f"Unexpected error while saving page: {page_data['url']} - Attempt {attempt}/{MAX_RETRIES}"
            )

    logger.error(
        f"Page '{page_data['url']}' failed to be saved after {MAX_RETRIES} attempts.")
    return False


def save_parsed_page_content(parsed_data: dict, logger: logging.Logger) -> bool:
    """
    Inserts or updates parsed page content in the database.

    :param parsed_data: Dictionary with keys: 'page_url', 'title', 'summary', 'content',
                        'content_hash', 'categories' (list of category names)
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with get_db() as db:
                existing = db.query(PageContent).filter_by(
                    page_url=parsed_data['page_url']).first()

                # Case 1: Page does not exist – insert new record
                if not existing:
                    categories = _get_or_create_categories(
                        db, parsed_data.get('categories', []))

                    new_content = PageContent(
                        # page_url can't be None
                        page_url=parsed_data['page_url'],
                        title=parsed_data.get('title'),
                        summary=parsed_data.get('summary'),
                        content=parsed_data.get('content'),
                        content_hash=parsed_data.get('content_hash'),
                        categories=categories
                    )
                    db.add(new_content)
                    logger.debug(
                        f"Inserted new parsed content for page URL: {parsed_data['page_url']}")
                    return True

                # Case 2: Page exists but content hasn't changed – skip
                if existing.content_hash == parsed_data.get('content_hash'):
                    logger.info(
                        f"Skipping update: No content change for page URL: {parsed_data['page_url']}")
                    return False

                # Case 3: Page exists and content changed – update record
                existing.title = parsed_data.get('title')
                existing.summary = parsed_data.get('summary')
                existing.content = parsed_data.get('content')
                existing.content_hash = parsed_data.get('content_hash')

                categories = _get_or_create_categories(
                    db, parsed_data.get('categories', []))
                existing.categories = categories

                logger.debug(
                    f"Updated parsed content for page URL: {parsed_data['page_url']}")
                return True

        except (IntegrityError, DataError) as e:
            logger.warning(
                f"Non-recoverable DB error on parsed page '{parsed_data['page_url']}': {e}")
            return False
        except OperationalError as e:
            logger.warning(
                f"OperationalError on parsed page '{parsed_data['page_url']}' - Attempt {attempt}/{MAX_RETRIES}: {e}"
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error while saving parsed page contents '{parsed_data['page_url']}' - Attempt {attempt}/{MAX_RETRIES}"
            )

    logger.error(
        f"Failed to save parsed page contents: {parsed_data['page_url']} after {MAX_RETRIES} retries.")
    return False


def _get_or_create_categories(db: Session, category_names: List[str]):
    """
    Ensures Category objects exist for each name in the list.

    :param db: SQLAlchemy session
    :param category_names: List of category names
    :return: List of Category objects
    """
    existing_categories = db.query(Category).filter(
        Category.name.in_(category_names)).all()

    existing_names = {cat.name for cat in existing_categories}
    new_names = set(category_names) - existing_names

    new_categories = [Category(name=name) for name in new_names]
    db.add_all(new_categories)

    # to get IDs for new categories
    db.flush()

    return existing_categories + new_categories
