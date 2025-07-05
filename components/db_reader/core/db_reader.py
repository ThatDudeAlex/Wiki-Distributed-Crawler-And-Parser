import logging
from contextlib import contextmanager
from database.engine import SessionLocal
from database.db_models.models import SeenUrlCache


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


def is_url_cached(url: str, logger: logging.Logger, session_factory=None) -> dict | None:
    """
    Checks if a URL exists in the SeenUrlCache in the database
    """
    with get_db(session_factory=session_factory) as db:
        try:
            # Try finding an existing cached url
            cached = db.query(SeenUrlCache).filter_by(url=url).first()
            if cached:
                logger.info(f"URL '{url}' found in DB cache")
                return {'url': cached.url, 'last_seen': cached.last_seen, "is_cached": True}

            logger.info(f"URL '{url}' not found in DB cache")
            return {'url': url, "is_cached": False}
        except Exception as e:
            # Re-raise after logging, so the API layer can handle it (e.g., return 500)
            logger.error('DB Cache check failed: %s (URL: %s)',
                         e, url, exc_info=True)
            raise
