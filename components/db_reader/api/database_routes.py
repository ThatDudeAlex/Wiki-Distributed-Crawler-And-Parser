from fastapi import APIRouter
from fastapi.applications import JSONResponse
from fastapi.encoders import jsonable_encoder
from shared.logging_utils import get_logger
from components.db_reader.core.db_reader import pop_links_from_schedule


database_router = APIRouter()
logger = get_logger("db_reader")


@database_router.get("/get_scheduled_links")
def pop_links(count: int):
    try:
        links = pop_links_from_schedule(count=count, logger=logger)
        if links:
            return JSONResponse(content=jsonable_encoder(links))
        return []
    except Exception as e:
        logger.error(
            f"Exception in pop_links_from_schedule: {e}", exc_info=True)
        return JSONResponse(content=[], status_code=500)
