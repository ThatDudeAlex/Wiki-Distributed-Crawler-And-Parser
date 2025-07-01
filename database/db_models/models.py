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

"""****  TABLE DEFINITIONS  ****"""


class Page(Base):
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
    content_hash = Column(String(2048), unique=True, nullable=True)
    compressed_filepath = Column(String(2048), unique=True, nullable=True)

    last_crawled_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    # TODO: see if this column is needed or if i can do it without it
    # next_crawl_at = Column(DateTime(timezone=True), nullable=True)

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
    __tablename__ = "links"

    source_page_url = Column(
        BigInteger,
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
        Index("idx_source_page_id", "source_page_id"),
    )


# Association table for many-to-many relationship
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

    # List of article page categories/tags
    # categories = Column(JSON, nullable=True)

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
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    pages = relationship(
        "PageContent",
        secondary=page_category_association,
        back_populates="categories"
    )
