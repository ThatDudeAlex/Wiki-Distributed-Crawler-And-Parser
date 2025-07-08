import logging
from contextlib import contextmanager
from database.engine import SessionLocal
from database.db_models.models import ScheduledLinks


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
