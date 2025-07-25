from fastapi import APIRouter
from fastapi.applications import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import SQLAlchemyError
from shared.logging_utils import get_logger
from components.db_reader.core.db_reader import pop_links_from_schedule, are_tables_empty


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


# TODO: uncomment once rescheduler component is done
# @database_router.get("/get_need_rescheduling")
# def pop_links(count: int):
#     try:
#         links = pop_links_from_schedule(count=count, logger=logger)
#         if links:
#             return JSONResponse(content=jsonable_encoder(links))
#         return []
#     except Exception as e:
#         logger.error(
#             f"Exception in pop_links_from_schedule: {e}", exc_info=True)
#         return JSONResponse(content=[], status_code=500)


@database_router.get("/tables/empty")
def verify_empty_tables():
    try:
        is_empty = are_tables_empty(logger=logger)
        return {"are_tables_empty": is_empty}
    except SQLAlchemyError as e:
        logger.error(
            f"Database error in verify_empty_tables: {e}", exc_info=True)
        return JSONResponse(content={"detail": "Database error occurred"}, status_code=500)
    except Exception as e:
        logger.error(
            f"Unexpected error in verify_empty_tables: {e}", exc_info=True)
        return JSONResponse(content={"detail": "Unexpected error occurred"}, status_code=500)
