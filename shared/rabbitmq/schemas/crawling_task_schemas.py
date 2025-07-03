from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal, Optional, Union
from pydantic import Field
from pydantic import BaseModel, HttpUrl
from shared.rabbitmq.enums.crawl_status import CrawlStatus
from shared.rabbitmq.types import QueueMsgSchemaInterface, ValidationError


# === Crawling Task (Scheduler → Crawler) ===

@dataclass
class CrawlTask(QueueMsgSchemaInterface):
    url: str
    scheduled_at: datetime
    depth: int = 0
    retry_count: Optional[int] = 0  # for if i want to track retries

    def validate(self) -> None:
        # verity that url exist and is valid url
        if not self.url or not self.is_valid_url(self.url):
            raise ValidationError("Invalid or missing URL", field="url")

        # verify that scheduled_at exist
        if not self.scheduled_at:
            raise ValidationError(
                "Missing scheduled_at value", field="scheduled_at")

        # If scheduled_at is a str, verify that it's a valid string
        if isinstance(self.scheduled_at, str):
            try:
                self.scheduled_at = datetime.fromisoformat(self.scheduled_at)
            except ValueError:
                raise ValidationError(
                    "scheduled_at must be a valid ISO 8601 string", field="scheduled_at")

        #  If scheduled_at is not a str, verify that it's a datatime object
        if not isinstance(self.scheduled_at, datetime):
            raise ValidationError(
                "scheduled_at must be a datetime object", field="scheduled_at")

        # Verify depth
        if not isinstance(self.depth, int) or self.depth < 0:
            raise ValidationError(
                "depth must be a non-negative integer", field="depth")

        if self.retry_count is not None and not isinstance(self.retry_count, int):
            raise ValidationError(
                "retry_count must be an integer", field="retry_count")


# === Crawl Metadata Message (Crawler → DB Writer) ===
@dataclass
class SavePageMetadataTask(QueueMsgSchemaInterface):
    status: CrawlStatus
    fetched_at: datetime
    url: str
    http_status_code: Optional[int] = None      # None if failed
    url_hash: Optional[str] = None              # None if failed
    html_content_hash: Optional[str] = None     # None if failed
    compressed_filepath: Optional[str] = None   # None if failed
    error_type: Optional[str] = None            # None if success
    error_message: Optional[str] = None         # None if success

    def validate(self) -> None:
        # Validate URL
        if not self.url or not self.is_valid_url(self.url):
            raise ValidationError("Invalid or missing URL", field="url")

        # Validate fetched_at
        if not isinstance(self.fetched_at, datetime):
            raise ValidationError(
                "fetched_at must be a datetime", field="fetched_at")

        # Validate status
        if not isinstance(self.status, CrawlStatus):
            raise ValidationError("Invalid crawl status value", field="status")

        if self.status == CrawlStatus.SUCCESS:
            # These must exist on success
            if self.error_type is not None or self.error_message is not None:
                raise ValidationError(
                    "error_type and error_message must be None on success", field="error_type")
            if self.http_status_code is None:
                raise ValidationError(
                    "http_status_code required on success", field="http_status_code")
            if not all([self.url_hash, self.html_content_hash, self.compressed_filepath]):
                raise ValidationError(
                    "All hashes and compressed_filepath are required on success")

        else:  # status is FAILED or SKIPPED
            if not self.error_type or not self.error_message:
                raise ValidationError(
                    "error_type and error_message are required on failure", field="error_type")

        # Optional: http_status_code must be int if present
        if self.http_status_code is not None and not isinstance(self.http_status_code, int):
            raise ValidationError(
                "http_status_code must be an integer", field="http_status_code")

# TODO: Remove if not needed


class FetchPageMetadata(BaseModel):
    url: HttpUrl
