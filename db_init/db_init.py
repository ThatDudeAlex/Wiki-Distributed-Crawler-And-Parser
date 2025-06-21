import os
import time
import sys
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    create_engine,
    Column,
    Integer,
    String,
    func,
)

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
MAX_RETRIES = 10
DELAY = 3  # seconds

Base = declarative_base()

"""****  ENUM DEFINITIONS  ****"""


crawl_status_enum = Enum(
    "PENDING",
    "CRAWLED_SUCCESS",
    "CRAWL_FAILED",
    "SKIPPED",
    name="crawl_status_enum",
    create_type=True,
)

"""****  TABLE DEFINITIONS  ****"""


class Page(Base):
    __tablename__ = 'pages'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    url = Column(String(2048), unique=True, nullable=False)
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
        server_default="PENDING",
    )
    http_status_code = Column(Integer, nullable=True)
    crawl_attempts = Column(Integer, nullable=False, default=0)

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

# TODO: this function can be repurposed into a general `wait_for`
#       and added to my python-utilities package


def wait_for_db():
    print("Waiting for the database to be ready...")
    retries = 0
    while retries < MAX_RETRIES:
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect():
                print("Database is ready!")
                return
        except OperationalError as e:
            print(
                f"Database not ready yet (attempt {retries + 1}/{MAX_RETRIES}): {e}")
            time.sleep(DELAY)
            retries += 1
    print("Exceeded maximum retry attempts. Exiting.")
    sys.exit(1)


if __name__ == "__main__":
    wait_for_db()
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print("Database initialized with tables.")
