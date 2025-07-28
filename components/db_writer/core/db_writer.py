import logging
from contextlib import contextmanager
from datetime import datetime
from typing import List

from database.db_models.models import (
    Category,
    Link,
    Page,
    PageContent,
    ScheduledLinks
)
from database.engine import SessionLocal
from shared.rabbitmq.enums.crawl_status import CrawlStatus
from shared.rabbitmq.schemas.save_to_db import (
    SaveLinksToSchedule,
    SavePageMetadataTask,
    SaveParsedContent,
    SaveProcessedLinks)
from sqlalchemy import case
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session


@contextmanager
def get_db(session_factory=None):
    session_factory = session_factory or SessionLocal
    db = session_factory()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger = logging.getLogger("db_writer")  # fallback global logger
        logger.error("DB transaction failed, rolling back: %s", e)
        db.rollback()
        raise
    finally:
        db.close()


def save_page_metadata(page_metadata: SavePageMetadataTask, logger: logging.Logger, session_factory=None):
    """
    Insert or update metadata about a crawled page into the database

    Performs an upsert on the Page table using the page's URL as the unique identifier.
    Increments crawl attempt counters and handles failed crawl tracking based on status.

    Args:
        page_metadata (SavePageMetadataTask): Structured data representing crawl metadata for a page
        logger (logging.Logger): Logger instance
        session_factory (optional): Optional custom SQLAlchemy session factory for testing or injection
    """
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
                next_crawl_at=page_metadata.next_crawl,
                total_crawl_attempts=1,
                failed_crawl_attempts=0,
                last_error_seen=page_metadata.error_message
            )

            # INSERT or UPDATE (aka Upsert)
            stmt = stmt.on_conflict_do_update(
                # Assumes `url` has a UNIQUE constraint
                index_elements=['url'],
                set_={
                    'last_crawl_status': stmt.excluded.last_crawl_status,
                    'http_status_code': stmt.excluded.http_status_code,
                    'html_content_hash': stmt.excluded.html_content_hash,
                    'last_crawled_at': stmt.excluded.last_crawled_at,
                    'next_crawl_at': stmt.excluded.next_crawl_at,
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
            logger.info("Succesfully inserted/updated into DB page: %s", page_metadata.url)

        except Exception as e:
            logger.error(
                "Unexpected error while fetching page metadata: %s, %s", page_metadata.url, e)


def save_processed_links(processed_links: SaveProcessedLinks, logger: logging.Logger, session_factory=None) -> None:
    """
    Bulk insert or update discovered hyperlinks into the Link table

    Performs a bulk upsert using ON CONFLICT DO UPDATE on (source_page_url, url).
    Each link includes metadata such as depth, anchor text, and HTML attributes.

    Args:
        processed_links (SaveProcessedLinks): Structured data containing all processed links from a parsed page
        logger (logging.Logger): Logger instance
        session_factory (optional): Optional custom SQLAlchemy session factory for testing or injection
    """
    with get_db(session_factory=session_factory) as db:
        try:
            if not processed_links.links:
                logger.warning("No links to insert")
                return

            values = []
            for link in processed_links.links:
                discovered_at_dt = datetime.fromisoformat(link.discovered_at)
                values.append({
                    'source_page_url': link.source_page_url,
                    'url': link.url,
                    'depth': link.depth,
                    'discovered_at': discovered_at_dt,
                    'is_internal': link.is_internal,
                    'anchor_text': link.anchor_text,
                    'title_attribute': link.title_attribute,
                    'rel_attribute': link.rel_attribute,
                    'id_attribute': link.id_attribute,
                    'link_type': link.link_type,
                })

            # Single bulk INSERT ... ON CONFLICT UPDATE
            stmt = insert(Link).values(values)

            stmt = stmt.on_conflict_do_update(
                index_elements=['source_page_url', 'url'],
                set_={
                    'anchor_text': stmt.excluded.anchor_text,
                    'title_attribute': stmt.excluded.title_attribute,
                    'rel_attribute': stmt.excluded.rel_attribute,
                    'id_attribute': stmt.excluded.id_attribute,
                    'link_type': stmt.excluded.link_type,
                }
            )

            db.execute(stmt)
            logger.info("Bulk upserted %d links into the Link table", len(values))

        except Exception:
            logger.exception("Unexpected error while bulk saving processed links")


def save_parsed_data(page_data: SaveParsedContent, logger: logging.Logger, session_factory=None) -> bool:
    """
    Save or update parsed textual content and categories for a crawled page

    If content already exists for the given source URL, it is updated. Otherwise,
    a new PageContent record is created. Also ensures all referenced categories exist.

    Args:
        page_data (SaveParsedContent): Structured data including title, text content,
            content hash, parsed timestamp, and associated category names
        logger (logging.Logger): Logger instance
        session_factory (optional): Optional SQLAlchemy session factory override

    Returns:
        bool: True if the operation succeeded, False if an error occurred
    """
    with get_db(session_factory=session_factory) as db:
        try:
            # Get or create categories
            category_objs = _get_or_create_categories(db, page_data.categories)

            # Insert or update PageContent
            existing_page = db.query(PageContent).filter_by(
                source_page_url=page_data.source_page_url).first()

            if existing_page:
                # Update existing fields
                existing_page.title = page_data.title
                existing_page.text_content = page_data.text_content
                existing_page.text_content_hash = page_data.text_content_hash
                existing_page.parsed_at = page_data.parsed_at
                existing_page.categories = category_objs  # update associations
            else:
                # Create new PageContent
                page = PageContent(
                    source_page_url=page_data.source_page_url,
                    title=page_data.title,
                    text_content=page_data.text_content,
                    text_content_hash=page_data.text_content_hash,
                    parsed_at=page_data.parsed_at,
                    categories=category_objs  # set relationship
                )
                db.add(page)

            logger.info("Parsed content saved for: %s", page_data.source_page_url)
            return True
        except Exception:
            logger.exception(
                "Unexpected error while saving parsed content: %s", page_data.source_page_url)
            return False


def add_links_to_schedule(links_to_schedule: SaveLinksToSchedule, logger: logging.Logger, session_factory=None) -> None:
    """
    Bulk insert new links into the ScheduledLinks table for future crawling

    Performs a bulk upsert using ON CONFLICT DO NOTHING to avoid duplicates based on URL.
    Each link includes its target URL, crawl depth, and the timestamp when it was scheduled.

    Args:
        links_to_schedule (SaveLinksToSchedule): Structured data containing links to be scheduled
        logger (logging.Logger): Logger instance
        session_factory (optional): Optional SQLAlchemy session factory for dependency injection or testing
    """
    with get_db(session_factory=session_factory) as db:
        values = []
        for link in links_to_schedule.links:
            values.append({
                "url": link.url,
                "scheduled_at": link.scheduled_at,
                'depth': link.depth
            })

        # Skip if no values
        if not values:
            logger.warning('Skipped scheduling links into the DB: no values received')
            return

        # Single bulk INSERT ... ON CONFLICT DO NOTHING
        stmt = insert(ScheduledLinks).values(values)
        stmt = stmt.on_conflict_do_nothing(index_elements=['url'])
        logger.info("Bulk inserted %d links into schedule table", len(values))
        try:
            db.execute(stmt)
        except Exception:
            logger.exception("Bulk insert into schedule_links failed")
            raise


# Makes sure Category objects exist for each name in the list.
def _get_or_create_categories(db: Session, category_names: List[str]) -> List[Category]:
    """
    Ensure that Category entries exist for all given names, and return the corresponding objects

    Looks up existing categories in bulk. Creates any missing ones and flushes them
    to get assigned IDs without committing. Useful for assigning category relationships.

    Args:
        db (Session): SQLAlchemy database session
        category_names (List[str]): List of category names to ensure in the database

    Returns:
        List[Category]: Combined list of existing and newly created Category objects
    """
    existing_categories = db.query(Category).filter(
        Category.name.in_(category_names)
    ).all()

    existing_names = {category.name for category in existing_categories}
    new_names = set(category_names) - existing_names

    new_categories = [Category(name=name) for name in new_names]
    db.add_all(new_categories)

    # to get IDs for new categories
    db.flush()

    return existing_categories + new_categories
