from enum import Enum as PyEnum
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
    func,
)

Base = declarative_base()

"""****  ENUM DEFINITIONS  ****"""


class CrawlStatus(PyEnum):
    PENDING = "PENDING"
    CRAWLED_SUCCESS = "CRAWLED_SUCCESS"
    CRAWL_FAILED = "CRAWL_FAILED"
    SKIPPED = "SKIPPED"


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
    url_hash = Column(String(2048), unique=True, nullable=False)
    title = Column(String(512), nullable=True)

    last_crawled_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    next_crawl_at = Column(DateTime(timezone=True), nullable=True)

    last_crawl_status = Column(
        crawl_status_enum,
        nullable=False,
        server_default=CrawlStatus.PENDING.value,
    )
    http_status_code = Column(Integer, nullable=True)
    crawl_attempts = Column(Integer, nullable=False, default=1)

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
        Index("idx_pages_title", "title"),
        Index("idx_last_crawled", "last_crawled_at"),
        Index("idx_next_crawl", "next_crawl_at"),
        Index("idx_last_crawl_status", "last_crawl_status"),
    )


class Link(Base):
    __tablename__ = "links"

    source_page_id = Column(
        BigInteger,
        ForeignKey("pages.id", ondelete="CASCADE"),
        primary_key=True,
    )
    target_url = Column(String(2048), primary_key=True)
    link_text = Column(String(512), nullable=True)
    is_internal = Column(Boolean, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    source_page = relationship("Page", back_populates="links")

    __table_args__ = (
        Index("idx_source_page_id", "source_page_id"),
    )
