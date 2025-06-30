from dataclasses import dataclass
from pydantic import BaseModel, HttpUrl, FilePath


class ParsingTaskSchema(BaseModel):
    url: HttpUrl
    compressed_path: FilePath


@dataclass
class ParsingTask:
    url: str
    compressed_path: str
