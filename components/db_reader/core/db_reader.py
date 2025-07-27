import datetime
import logging
from contextlib import contextmanager
from zoneinfo import ZoneInfo

from sqlalchemy.orm import aliased

from database.engine import SessionLocal
from database.db_models.models import Link, Page, PageContent, ScheduledLinks


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


def pop_links_from_schedule(count: int, logger: logging.Logger, session_factory=None) -> list | None:
    with get_db(session_factory=session_factory) as db:
        scheduled_links = (
            db.query(ScheduledLinks)
            .order_by(ScheduledLinks.id)
            .limit(count)
            .with_for_update(skip_locked=True)
            .all()
        )

        if not scheduled_links:
            return []

        links = []

        for link in scheduled_links:
            links.append({
                'url': link.url,
                'scheduled_at': link.scheduled_at,
                'depth': link.depth
            })

        logger.info(f'Fetched links: {scheduled_links}')

        ids = [link.id for link in scheduled_links]

        db.query(ScheduledLinks).filter(
            ScheduledLinks.id.in_(ids)
        ).delete(synchronize_session=False)

        db.commit()

        return links


def are_tables_empty(logger: logging.Logger, session_factory=None) -> bool:
    with get_db(session_factory=session_factory) as db:
        # Count rows in the relevant tables
        page_count = db.query(Page).count()
        page_content_count = db.query(PageContent).count()
        scheduled_links_count = db.query(ScheduledLinks).count()

        # Check if all tables are empty (this is the trigger to seed the rabbitMQ queue)
        if not page_count and not page_content_count and not scheduled_links_count:
            logger.info(
                "The DB tables are empty - this is a fresh instance of the DB")
            return True

        return False


def get_due_pages(logger: logging.Logger, session_factory=None) -> list[str] | None:
    with get_db(session_factory=session_factory) as db:
        eastern = ZoneInfo("America/New_York")
        now_est = datetime.datetime.now(eastern)

        logger.info("In get_due_pages")

        LinkAlias = aliased(Link)

        results = (
            db.query(Page.url, LinkAlias.depth)
            .outerjoin(LinkAlias, LinkAlias.url == Page.url)
            .filter(
                Page.next_crawl_at != None,
                Page.next_crawl_at < now_est
            )
            .order_by(Page.next_crawl_at.asc())
            .all()
        )

        logger.info(f"Found {len(results)} pages due for recrawl")

        return [
            {"url": url, "depth": depth if depth is not None else 0}
            for url, depth in results
        ]