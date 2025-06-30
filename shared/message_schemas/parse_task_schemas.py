from pydantic import BaseModel, HttpUrl, FilePath


class ParseDonwloadedPageTask(BaseModel):
    url: HttpUrl
    compressed_path: FilePath
