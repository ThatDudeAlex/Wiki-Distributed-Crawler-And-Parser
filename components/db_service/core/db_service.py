from contextlib import contextmanager
import logging
from typing import List

from sqlalchemy import case
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from database.engine import SessionLocal
from database.db_models.models import Category, Page, PageContent
from shared.rabbitmq.enums.crawl_status import CrawlStatus
from shared.rabbitmq.types import ParsedContent
from shared.rabbitmq.schemas.crawling_task_schemas import SavePageMetadataTask


@contextmanager
def get_db(session_factory=None):
    session_factory = session_factory or SessionLocal
    db = session_factory()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

# TODO: Remove if not needed


def fetch_page_metadata(url: str, logger: logging.Logger, session_factory=None):
    with get_db(session_factory=session_factory) as db:
        try:
            # Try finding an existing page by URL
            res = db.query(Page).filter_by(url=url).first()
            if res:
                logger.info(
                    f"Found Page: ID = {res.id}, URL = {res.url}, Status = {res.last_crawl_status}")
            else:
                logger.warning('No entry fround for URL: %s', url)

            return db.query(Page).filter_by(url=url).first()
        except Exception:
            logger.exception(
                "Unexpected error while fetching page metadata: %s", url)


# TODO: UPDATE the on_conflict_do_update to only change what's needed!
def save_page_metadata(page_metadata: SavePageMetadataTask, logger: logging.Logger, session_factory=None):
    with get_db(session_factory=session_factory) as db:
        try:
            stmt = insert(Page).values(
                url=page_metadata.url,
                last_crawl_status=page_metadata.status.value,
                http_status_code=page_metadata.http_status_code,
                url_hash=page_metadata.url_hash,
                html_content_hash=page_metadata.html_content_hash,
                compressed_filepath=page_metadata.compressed_filepath,
                last_crawled_at=page_metadata.fetched_at,
                total_crawl_attempts=1,
                failed_crawl_attempts=0,
                last_error_seen=page_metadata.error_message
            )

            # INSERT or UPDATE (aka Upsert)
            # IMPORTANT: This can causes an update of EVERY column even if it's not needed
            # It's fine to do on a low-scale (less than 1k+ upserts per second)
            stmt = stmt.on_conflict_do_update(
                # Assumes `url` has a UNIQUE constraint
                index_elements=['url'],
                set_={
                    'last_crawl_status': stmt.excluded.last_crawl_status,
                    'http_status_code': stmt.excluded.http_status_code,
                    'url_hash': stmt.excluded.url_hash,
                    'html_content_hash': stmt.excluded.html_content_hash,
                    'compressed_filepath': stmt.excluded.compressed_filepath,
                    'last_crawled_at': stmt.excluded.last_crawled_at,
                    'last_error_seen': stmt.excluded.last_error_seen,
                    'total_crawl_attempts': Page.total_crawl_attempts + 1,
                    'failed_crawl_attempts': case(
                        (
                            stmt.excluded.last_crawl_status.in_(
                                [CrawlStatus.FAILED.value, CrawlStatus.SKIPPED.value]),
                            Page.failed_crawl_attempts + 1
                        ),
                        else_=Page.failed_crawl_attempts
                    )
                }
            )
            db.execute(stmt)
        except Exception:
            logger.exception(
                "Unexpected error while fetching page metadata: %s", page_metadata.url)


def save_parsed_data(page_data: ParsedContent, logger: logging.Logger, session_factory=None) -> bool:
    with get_db(session_factory=session_factory) as db:
        try:
            stmt = insert(PageContent).values(
                source_page_url=page_data.source_page_url,
                title=page_data.title,
                summary=page_data.summary,
                text_content=page_data.text_content,
                text_content_hash=page_data.text_content_hash,
                parsed_at=page_data.parsed_at,
            )

            # TODO: Implement inserting categories into their own table
            db.execute(stmt)
        except Exception:
            logger.exception(
                "Unexpected error while saving parsed content: %s", page_data.source_page_url)


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
