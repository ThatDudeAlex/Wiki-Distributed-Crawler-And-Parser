import logging
from database.db_models.models import Page, Link
from database.engine import SessionLocal


class DatabaseService:
    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._db = SessionLocal()

    def save_page(self, crawl_data: tuple[str, str, str, str, int]):
        r"""Adds a new ``Page`` into the database. Returns ``page_id``.

        :param crawl_data: Tuple containing ``(url, url_hash, filepath, crawl_status, status_code)``.
        """
        if len(crawl_data) != 5:
            raise ValueError(
                f"Expected 5 items, got {len(crawl_data)}: {crawl_data}")

        url, url_hash, filepath, crawl_status, status_code = crawl_data
        page = Page(
            url=url,
            url_hash=url_hash,
            last_crawl_status=crawl_status,
            http_status_code=status_code,
            compressed_path=filepath)
        self._db.add(page)
        self._db.commit()
        return page.id

    def save_link(self, page_id, target_url, is_internal=False):
        link = Link(
            source_page_id=page_id,
            target_url=target_url,
            is_internal=is_internal
        )
        self._db.add(link)
        self._db.commit()
