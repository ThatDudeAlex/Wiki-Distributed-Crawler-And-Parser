from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import SQLAlchemyError
from components.db_reader.monitoring.metrics import DB_READER_REQUESTS_FAILURES_TOTAL, DB_READER_REQUESTS_RECEIVED_TOTAL
from shared.logging_utils import get_logger
from components.db_reader.core.db_reader import get_due_pages, pop_links_from_schedule, are_tables_empty


database_router = APIRouter()
logger = get_logger("db_reader")


@database_router.get("/get_scheduled_links", response_model=list[dict], status_code=200)
def pop_links(count: int):
    try:
        links = pop_links_from_schedule(count=count, logger=logger)
        DB_READER_REQUESTS_RECEIVED_TOTAL.labels(status="valid", operation="pop_links_from_schedule").inc()
        return JSONResponse(content=jsonable_encoder(links))
    except Exception as e:
        logger.error("Exception in pop_links_from_schedule: %s", e, exc_info=True)
        DB_READER_REQUESTS_FAILURES_TOTAL.labels(error_type="UnexpectedError").inc()
        DB_READER_REQUESTS_RECEIVED_TOTAL.labels(status="error", operation="pop_links_from_schedule").inc()
        return JSONResponse(content=[], status_code=500)



@database_router.get("/get_need_rescheduling", response_model=list[str], status_code=200)
def get_pages_need_recrawling():
    """
    Get a list of URLs that are due for recrawling (rescheduling)
    """
    try:
        pages = get_due_pages(logger=logger)
        DB_READER_REQUESTS_RECEIVED_TOTAL.labels(status="valid", operation="get_due_pages").inc()
        return JSONResponse(content=jsonable_encoder(pages))
    except Exception as e:
        logger.error("Exception in get_due_pages: %s", e, exc_info=True)
        DB_READER_REQUESTS_FAILURES_TOTAL.labels(error_type="UnexpectedError").inc()
        DB_READER_REQUESTS_RECEIVED_TOTAL.labels(status="error", operation="get_due_pages").inc()
        return JSONResponse(content={"error": "Internal Server Error"}, status_code=500)



@database_router.get("/tables/empty", status_code=200)
def verify_empty_tables():
    """
    Check if the Pages and Links tables are empty (used for seeding logic).
    """
    try:
        is_empty = are_tables_empty(logger=logger)
        DB_READER_REQUESTS_RECEIVED_TOTAL.labels(status="valid", operation="are_tables_empty").inc()
        return {"are_tables_empty": is_empty}
    except SQLAlchemyError as e:
        logger.error("Database error in verify_empty_tables: %s", e, exc_info=True)
        DB_READER_REQUESTS_FAILURES_TOTAL.labels(error_type="SQLAlchemyError").inc()
        DB_READER_REQUESTS_RECEIVED_TOTAL.labels(status="error", operation="are_tables_empty").inc()
        return JSONResponse(content={"detail": "Database error occurred"}, status_code=500)
    except Exception as e:
        logger.error("Unexpected error in verify_empty_tables: %s", e, exc_info=True)
        DB_READER_REQUESTS_FAILURES_TOTAL.labels(error_type="UnexpectedError").inc()
        DB_READER_REQUESTS_RECEIVED_TOTAL.labels(status="error", operation="are_tables_empty").inc()
        return JSONResponse(content={"detail": "Unexpected error occurred"}, status_code=500)
