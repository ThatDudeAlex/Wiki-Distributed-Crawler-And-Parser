from datetime import datetime
import hashlib
from zoneinfo import ZoneInfo


def create_hash(content: str) -> str:
    # Create a SHA-256 hash object
    hash_object = hashlib.sha256()

    # Update the hash object with the bytes of the url string
    hash_object.update(content.encode())

    # return the hexadecimal representation of the hash
    return hash_object.hexdigest()


def get_timestamp_eastern_time(isoformat: bool = False) -> datetime | str:
    """Returns an isoformat timestamp in timezone: America/New_York"""
    if isoformat:
        return datetime.now(ZoneInfo("America/New_York")).isoformat()

    return datetime.now(ZoneInfo("America/New_York"))
