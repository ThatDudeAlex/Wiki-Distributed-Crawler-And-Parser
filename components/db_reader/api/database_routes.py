from fastapi import APIRouter, HTTPException
from fastapi.applications import JSONResponse
from shared.logging_utils import get_logger
from components.db_reader.core.db_reader import is_url_cached


database_router = APIRouter()
logger = get_logger("db_reader")


@database_router.get("/url_cache")
def is_url_cached_endpoint(url: str):
    try:
        return is_url_cached(url=url, logger=logger)
    except Exception as e:
        logger.error(
            f"Exception in is_url_cached_endpoint: {e}", exc_info=True)
        return {'url': url, "is_cached": False}
