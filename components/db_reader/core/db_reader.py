import logging
from contextlib import contextmanager

from sqlalchemy.orm import aliased

from database.engine import SessionLocal
from database.db_models.models import Link, Page, PageContent, ScheduledLinks
from shared.utils import get_timestamp_eastern_time

from components.db_reader.monitoring.metrics import (
    DB_READER_LINKS_POPPED_TOTAL,
    DB_READER_DUE_PAGES_FOUND_TOTAL,
    DB_READER_EMPTY_CHECKS_TOTAL,
    DB_READER_QUERY_LATENCY_SECONDS,
)

@contextmanager
def get_db(session_factory=None):
    """
    Provides a transactional DB session with commit/rollback logic
    """
    session_factory = session_factory or SessionLocal
    db = session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def pop_links_from_schedule(count: int, logger: logging.Logger, session_factory=None) -> list[dict]:
    """
    Fetches a batch of scheduled links for crawling and removes them from the schedule

    This function:
    - Retrieves scheduled links while skipping any that are currently locked by other workers (using skip-locked)
    - Logs the number of fetched links
    - Deletes the fetched links from the `ScheduledLinks` table to avoid reprocessing
    - Returns a list of dicts with `url`, `scheduled_at`, and `depth` for each link

    Args:
        count (int): The number of links to retrieve
        logger (logging.Logger): Logger instance
        session_factory (optional): Custom SQLAlchemy session factory for testing or override

    Returns:
        list[dict]: A list of scheduled link metadata dictionaries
    """
    with get_db(session_factory) as db:
        with DB_READER_QUERY_LATENCY_SECONDS.labels(operation="pop_links_from_schedule").time():
            scheduled_links = (
                db.query(ScheduledLinks)
                .order_by(ScheduledLinks.id)
                .limit(count)
                .with_for_update(skip_locked=True)
                .all()
            )

            if not scheduled_links:
                return []

            logger.info("Fetched %d links from scheduled queue", len(scheduled_links))
            DB_READER_LINKS_POPPED_TOTAL.inc(len(scheduled_links))

            links = [
                {
                    'url': link.url,
                    'scheduled_at': link.scheduled_at,
                    'depth': link.depth
                }
                for link in scheduled_links
            ]

            ids = [link.id for link in scheduled_links]
            db.query(ScheduledLinks).filter(ScheduledLinks.id.in_(ids)).delete(synchronize_session=False)

            return links

def are_tables_empty(logger: logging.Logger, session_factory=None) -> bool:
    """
    Checks if the core database tables (Page, PageContent, ScheduledLinks) are empty

    This is primarily used at service startup to determine whether the database is
    in a fresh state and requires initial seeding

    Args:
        logger (logging.Logger): Logger instance
        session_factory (optional): Custom SQLAlchemy session factory (used for testing or override)

    Returns:
        bool: True if all relevant tables are empty, False otherwise.
    """
    with get_db(session_factory=session_factory) as db:
        with DB_READER_QUERY_LATENCY_SECONDS.labels(operation="are_tables_empty").time():
            page_count = db.query(Page).count()
            page_content_count = db.query(PageContent).count()
            scheduled_links_count = db.query(ScheduledLinks).count()

        is_empty = not page_count and not page_content_count and not scheduled_links_count
        DB_READER_EMPTY_CHECKS_TOTAL.labels(empty=str(is_empty).lower()).inc()

        if is_empty:
            logger.info("The DB tables are empty - this is a fresh instance of the DB")

        return is_empty

def get_due_pages(logger: logging.Logger, session_factory=None) -> list[dict]:
    """
    Retrieves a list of pages that are scheduled to be recrawled

    A page is considered due for recrawl if:
    - Its `next_crawl_at` timestamp is set
    - The `next_crawl_at` timestamp is earlier than the current time (America/New_York)

    The result includes the URL and its associated crawl depth, which is obtained
    via an outer join with the Link table.

    Args:
        logger (logging.Logger): Logger instance 
        session_factory (optional): Custom SQLAlchemy session factory (used for testing or override)

    Returns:
        list[dict]: A list of dictionaries with 'url' and 'depth' keys for each due page.
    """
    with get_db(session_factory) as db:
        now_est = get_timestamp_eastern_time()
        logger.info("Searching for pages due for recrawl")

        with DB_READER_QUERY_LATENCY_SECONDS.labels(operation="get_due_pages").time():
            LinkAlias = aliased(Link)

            results = (
                db.query(Page.url, LinkAlias.depth)
                .outerjoin(LinkAlias, LinkAlias.url == Page.url)
                .filter(
                    Page.next_crawl_at is not None,
                    Page.next_crawl_at < now_est
                )
                .order_by(Page.next_crawl_at.asc())
                .all()
            )

        logger.info("Found %d pages due for recrawl", len(results))
        DB_READER_DUE_PAGES_FOUND_TOTAL.inc(len(results))

        return [
            {"url": url, "depth": depth or 0}
            for url, depth in results
        ]
