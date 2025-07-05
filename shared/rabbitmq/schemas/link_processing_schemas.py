from dataclasses import dataclass
from typing import List
from datetime import datetime
from shared.rabbitmq.types import QueueMsgSchemaInterface, ValidationError
from shared.rabbitmq.schemas.parsing_task_schemas import LinkData, ProcessDiscoveredLinks


# === Save Link Record (Scheduler → DB Writer) ===

@dataclass
class SaveProcessedLinks(ProcessDiscoveredLinks):
    # Only inherits from ProcessDiscoveredLinks beccause it's
    # semantically different but structurally the same
    pass


@dataclass
class SeenUrl(QueueMsgSchemaInterface):
    url: str
    last_seen: datetime

    def _validate(self) -> None:
        # Validate source_page_url
        if not self.url or not self.is_valid_url(self.url):
            raise ValidationError("Invalid or missing url", field="url")

    def validate_publish(self) -> None:
        self._validate()
        if not isinstance(self.last_seen, datetime):
            raise ValidationError(
                "last_seen must be a datetime object before publishing", field="last_seen")
        # Convert to ISO string for JSON serialization
        self.last_seen = self.last_seen.isoformat()

    def validate_consume(self) -> None:
        if not isinstance(self.last_seen, str):
            raise ValidationError(
                "last_seen must be a ISO 8601 string when consuming", field="last_seen")

        try:
            # convert to datetime
            self.last_seen = datetime.fromisoformat(self.last_seen)
        except ValueError:
            raise ValidationError(
                "last_seen must be a valid ISO 8601 datetime string", field="last_seen")
        self._validate()


@dataclass
class CacheSeenUrls(QueueMsgSchemaInterface):
    seen_urls: List[SeenUrl]

    def _validate(self) -> None:
        if not isinstance(self.seen_urls, list) or not self.seen_urls:
            raise ValidationError(
                "seen_urls must be a non-empty list", field="seen_urls")

    def validate_publish(self) -> None:
        self._validate()

        # Validate each SeenUrl using publish context
        for i, link in enumerate(self.seen_urls):
            if not isinstance(link, SeenUrl):
                raise ValidationError(
                    f"links[{i}] must be a SeenUrl instance", field=f"seen_urls[{i}]")
            try:
                link.validate_publish()
            except ValidationError as e:
                raise ValidationError(str(e), field=f"seen_urls[{i}]")

    def validate_consume(self) -> None:
        # Convert url dicts to SeenUrl instances
        for i, url in enumerate(self.seen_urls):
            if isinstance(url, dict):
                try:
                    self.seen_urls[i] = SeenUrl(**url)
                except Exception as e:
                    raise ValidationError(
                        f"Failed to parse url[{i}]: {e}", field=f"seen_urls[{i}]")

            try:
                self.seen_urls[i].validate_consume()
            except ValidationError as e:
                raise ValidationError(str(e), field=f"seen_urls[{i}]")
