from fastapi import APIRouter

from shared.utils import get_timestamp_eastern_time


monitor_router = APIRouter()

# TODO: decide if i should addd a /health endpoint to each component
@monitor_router.get("/health", status_code=200, tags=["monitoring"])
def health_check():
    """
    Health check endpoint for the db_reader component.
    Returns current timestamp in America/New_York timezone.
    """
    return {
        "status": "ok",
        "service": "db_reader_api",
        "timestamp": get_timestamp_eastern_time(isoformat=True)
    }
