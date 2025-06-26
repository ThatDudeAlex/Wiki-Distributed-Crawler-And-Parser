import logging
from database.db_models.models import Page, Link, CrawlStatus
from database.engine import SessionLocal


class DatabaseService:
    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._db = SessionLocal()

    def save_crawled_page(self, crawl_data: tuple[str, str, str, int]):
        r"""Adds a new ``Page`` into the database. Returns ``page_id``

        :param crawl_data: Tuple containing ``(url, url_hash, filepath, status_code)``
        """
        if len(crawl_data) != 5:
            raise ValueError(
                f"Expected 4 items, got {len(crawl_data)}: {crawl_data}")

        url, url_hash, filepath, status_code = crawl_data
        page = Page(
            url=url,
            url_hash=url_hash,
            last_crawl_status=CrawlStatus.CRAWLED_SUCCESS,
            http_status_code=status_code,
            compressed_path=filepath)
        self._db.add(page)
        self._db.commit()
        return page.id

    def _save_uncrawled_page(self, url: str, crawl_status: CrawlStatus, status_code: int) -> int:
        page = Page(
            url=url,
            last_crawl_status=crawl_status,
            http_status_code=status_code,
        )
        self._db.add(page)
        self._db.commit()
        return page.id

    def save_skipped_page(self, url: str, status_code: int) -> int:
        r"""Adds a page with ``CrawlStatus.SKIPPED`` into the database. Returns ``page_id``

        :param url: the ``url`` of the page being skipped

        :param status_code: the ``HTTP Status Code`` of the request
        """
        return self._save_uncrawled_page(url, CrawlStatus.SKIPPED, status_code)

    def save_failed_page_crawl(self, url: str, status_code: int) -> int:
        r"""Adds a page with ``CrawlStatus.CRAWL_FAILED`` into the database. Returns ``page_id``

        :param url: the ``url`` of the page that failed to be crawl

        :param status_code: the ``HTTP Status Code`` of the failed request
        """
        return self._save_uncrawled_page(url, CrawlStatus.CRAWL_FAILED, status_code)

    def save_link(self, page_id, target_url, is_internal=False):
        link = Link(
            source_page_id=page_id,
            target_url=target_url,
            is_internal=is_internal
        )
        self._db.add(link)
        self._db.commit()
