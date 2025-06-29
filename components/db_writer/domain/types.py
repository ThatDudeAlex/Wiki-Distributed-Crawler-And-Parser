# TODO: cleanup these comments when done
# pydantic throws ValidationError when failed
from pydantic import BaseModel, HttpUrl, FilePath
from database.db_models.models import CrawlStatus


class SavePageTask(BaseModel):
    url: HttpUrl
    url_hash: str
    crawl_status: CrawlStatus
    compressed_path: FilePath
    crawl_time: str
    status_code: int
