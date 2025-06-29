import logging
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.db_models.models import Base, CrawlStatus, Page, PageContent
from components.db_writer.core.db_writer import save_crawled_page, save_parsed_page_content


# Set up logger
logger = logging.getLogger("test_logger")
logger.setLevel(logging.DEBUG)


def test_save_crawled_page_real_postgres():
    with PostgresContainer("postgres:15") as pg:
        db_url = pg.get_connection_url()
        test_engine = create_engine(db_url)
        TestingSessionLocal = sessionmaker(bind=test_engine)

        # Create schema
        Base.metadata.create_all(test_engine)

        test_data = {
            "url": "http://example.com",
            "url_hash": "hash123",
            "last_crawl_status": CrawlStatus.CRAWLED_SUCCESS,
            "status_code": 200,
            "compressed_path": "/path/to/file",
            "crawl_time": "2025-01-01T12:00:00"
        }

        # Pass session factory explicitly
        success = save_crawled_page(
            test_data, logger, session_factory=TestingSessionLocal)
        assert success is True

        # Verify it worked
        with TestingSessionLocal() as session:
            page = session.query(Page).filter_by(
                url="http://example.com").first()
            assert page is not None
            assert page.url_hash == "hash123"
            assert page.http_status_code == 200


def test_save_parsed_page_content_real_postgres():
    with PostgresContainer("postgres:15") as pg:
        engine = create_engine(pg.get_connection_url())
        TestingSessionLocal = sessionmaker(bind=engine)

        # Create tables
        Base.metadata.create_all(engine)

        # Step 1: Insert a Page (required for foreign key)
        with TestingSessionLocal() as session:
            session.add(Page(
                url="http://example.com",
                url_hash="hash123",
                last_crawled_at="2025-01-01T12:00:00",
                compressed_path="/path/to/file",
                http_status_code=200,
                last_crawl_status=CrawlStatus.CRAWLED_SUCCESS,
                crawl_attempts=1
            ))
            session.commit()

        # Step 2: Save parsed content
        parsed_data = {
            "page_url": "http://example.com",
            "title": "Example Page",
            "summary": "Summary of the page",
            "content": "Full content",
            "content_hash": "hash-abc",
            "categories": ["Tech", "Python"]
        }

        success = save_parsed_page_content(
            parsed_data, logger, session_factory=TestingSessionLocal)
        assert success is True

        # Step 3: Verify
        with TestingSessionLocal() as session:
            content = session.query(PageContent).filter_by(
                page_url="http://example.com").first()
            assert content is not None
            assert content.title == "Example Page"
            assert len(content.categories) == 2
