
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from urllib.parse import urlparse


@dataclass
class QueueMsgSchemaInterface(ABC):
    """Base class for all rabbitmq message schemas"""

    def to_dict(self) -> dict:
        return asdict(self)

    def is_valid_url(self, url: str) -> bool:
        if not isinstance(url, str):
            return False
        result = urlparse(url)
        return all([result.scheme, result.netloc])

    @abstractmethod
    def validate_publish(self) -> None:
        pass

    @abstractmethod
    def validate_consume(self) -> None:
        pass


class ValidationError(Exception):
    """Raised when a message schema fails validation"""

    def __init__(self, message: str, field: str = None):
        self.field = field
        full_msg = f"{field}: {message}" if field else message
        super().__init__(full_msg)
