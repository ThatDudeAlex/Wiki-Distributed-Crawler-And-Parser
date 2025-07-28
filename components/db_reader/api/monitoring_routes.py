import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter


monitor_router = APIRouter()

# TODO: decide if i should addd a /health endpoint to each component
@monitor_router.get("/health", status_code=200, tags=["monitoring"])
def health_check():
    """
    Health check endpoint for the db_reader component.
    Returns current timestamp in America/New_York timezone.
    """
    now_est = datetime.now(ZoneInfo("America/New_York"))
    return {
        "status": "ok",
        "service": "db_reader_api",
        "timestamp": now_est.isoformat()
    }
