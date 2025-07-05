from fastapi import APIRouter


monitor_router = APIRouter()


@monitor_router.get("/health")
def health_check():
    return {"status": "ok", "service": "db_reader_api"}
