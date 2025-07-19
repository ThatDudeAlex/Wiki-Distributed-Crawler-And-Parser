from pydantic import BaseModel, field_validator
from urllib.parse import urlparse

class ParsingTask(BaseModel):
    url: str
    depth: int
    compressed_filepath: str

    @field_validator("url")
    @classmethod
    def must_be_valid_url(cls, url: str) -> str:
        result = urlparse(url)
        if not (result.scheme and result.netloc):
            raise ValueError("Invalid URL format")
        return url
    
    @field_validator("depth")
    @classmethod
    def validate_depth(cls, depth: int) -> int:
        if depth < 0:
            raise ValueError("Depth must be a non-negative integer")
        return depth