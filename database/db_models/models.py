from shared.rabbitmq.enums.crawl_status import CrawlStatus
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Column,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)

Base = declarative_base()

"""****  ENUM DEFINITIONS  ****"""

crawl_status_enum = SqlEnum(
    CrawlStatus,
    name="crawl_status_enum",
    create_type=True,
)

# TODO: split tables into their own files

"""****  TABLE DEFINITIONS  ****"""


class Page(Base):
    """
    Represents a crawled web page and stores crawl-related metadata.

    Fields:
        - url: Unique URL of the page.
        - last_crawl_status: Result of the most recent crawl attempt.
        - http_status_code: HTTP response status from last crawl.
        - url_hash, html_content_hash: Help detect duplicate or changed pages.
        - compressed_filepath: Filepath to stored HTML content.
        - last_crawled_at, next_crawl_at: Crawl scheduling.
        - total_crawl_attempts, failed_crawl_attempts: Retry tracking.
        - last_error_seen: Optional crawl failure info.
        - created_at, updated_at: Timestamps.
    
    Relationships:
        - links: Outgoing hyperlinks discovered on this page.
        - parsed_page: One-to-one relationship with PageContent.
    """
    __tablename__ = 'pages'
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    url = Column(String(2048), unique=True, nullable=False)
    last_crawl_status = Column(
        crawl_status_enum,
        nullable=False,
    )
    http_status_code = Column(Integer, nullable=True)

    # Hashes and filepath are all unique
    url_hash = Column(String(2048), unique=True, nullable=True)
    html_content_hash = Column(String(2048), unique=True, nullable=True)
    compressed_filepath = Column(String(2048), unique=True, nullable=True)

    last_crawled_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    # TODO: uncomment once recrawl is implemented
    next_crawl_at = Column(DateTime(timezone=True), nullable=True)

    total_crawl_attempts = Column(Integer, nullable=False, default=1)
    failed_crawl_attempts = Column(Integer, nullable=False, default=0)

    last_error_seen = Column(String(2048), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),  # Sets the current time every time the row is updated
        nullable=False,
    )

    # relationship to Link
    links = relationship(
        "Link",
        back_populates="source_page",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_pages_url", "url"),
        Index("idx_last_crawled", "last_crawled_at"),
        # Index("idx_next_crawl", "next_crawl_at"),
        Index("idx_last_crawl_status", "last_crawl_status"),
    )


class Link(Base):
    """
    Represents a hyperlink discovered during parsing of a source page.

    Composite Primary Key:
        - (source_page_url, url): Prevents duplicate links from the same source.

    Fields:
        - url: Target URL the link points to.
        - depth: Distance from seed page.
        - is_internal: Whether it's in-domain.
        - anchor_text, id/rel/title/link_type: HTML attributes.
        - discovered_at, created_at: Metadata timestamps.

    Relationships:
        - source_page: Many-to-one relationship with Page.
    """
    __tablename__ = "links"

    source_page_url = Column(
        String(2048),
        ForeignKey("pages.url", ondelete="CASCADE"),
        primary_key=True,
    )
    url = Column(String(2048), primary_key=True)
    depth = Column(Integer, nullable=False)

    is_internal = Column(Boolean, nullable=False)
    anchor_text = Column(String(512), nullable=True)

    id_attribute = Column(String(512), nullable=True)
    rel_attribute = Column(String(512), nullable=True)
    title_attribute = Column(String(512), nullable=True)

    link_type = Column(String(512), nullable=True)

    discovered_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    source_page = relationship("Page", back_populates="links")

    __table_args__ = (
        Index("idx_source_page_id", "source_page_url"),
    )


class ScheduledLinks(Base):
    """
    Stores links that have been queued for crawling by the scheduler.

    Fields:
        - url: The URL to crawl.
        - depth: Crawl depth of this link.
        - scheduled_at: Timestamp when it was scheduled.
    
    Used by:
        - Scheduler to queue links.
        - Dispatcher to convert queued links into crawl tasks.
    """
    __tablename__ = "scheduled_links"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    url = Column(String(2048), unique=True, nullable=False)
    depth = Column(Integer, nullable=False)
    scheduled_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


"""
    Association table mapping pages to categories.

    Used in the many-to-many relationship between PageContent and Category.
    Each row links one page to one category.
"""
page_category_association = Table(
    'page_categories',
    Base.metadata,
    Column('page_url', Integer, ForeignKey(
        'page_content.id', ondelete="CASCADE"), primary_key=True),
    Column('category_id', Integer, ForeignKey(
        'categories.id', ondelete="CASCADE"), primary_key=True),
    UniqueConstraint('page_url', 'category_id', name='uix_page_category')
)


class PageContent(Base):
    """
    Stores extracted content from a successfully parsed page.

    Fields:
        - source_page_url: FK to the original Page.
        - title, summary: Headline and opening paragraph (if present).
        - text_content: Extracted main body text of the article.
        - text_content_hash: For change detection.
        - parsed_at, created_at, updated_at: Timestamps.

    Relationships:
        - page: One-to-one with Page.
        - categories: Many-to-many with Category via association table.
    """
    __tablename__ = 'page_content'

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # FK relationship to the Page table
    source_page_url = Column(String(2048), ForeignKey(
        'pages.url', ondelete="CASCADE"), nullable=False, unique=True)

    title = Column(String(512), nullable=True)

    # the first paragraph in an article page (under title)
    summary = Column(Text, nullable=True)

    # The entire main article content
    text_content = Column(Text, nullable=True)

    # A hash of the entire page to help detect changes in the page content
    text_content_hash = Column(Text, nullable=True)

    parsed_at = Column(DateTime(timezone=True),
                       server_default=func.now(), nullable=False)

    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(
    ), onupdate=func.now(), nullable=False)

    # ORM relationship back to Page
    page = relationship("Page", backref="parsed_page", uselist=False)

    categories = relationship(
        "Category",
        secondary=page_category_association,
        back_populates="pages"
    )


class Category(Base):
    """
    Represents a semantic category (e.g., Wikipedia category) assigned to parsed pages.

    Fields:
        - name: Unique name of the category.

    Relationships:
        - pages: Many-to-many relationship with PageContent.
    """
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    pages = relationship(
        "PageContent",
        secondary=page_category_association,
        back_populates="categories"
    )
