from pydantic import BaseModel, HttpUrl, FilePath


class ParsingTask(BaseModel):
    url: HttpUrl
    compressed_path: FilePath
