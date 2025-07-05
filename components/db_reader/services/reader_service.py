
from fastapi import FastAPI
import uvicorn
from components.db_reader.api.database_routes import database_router
from components.db_reader.api.monitoring_routes import monitor_router
from shared.logging_utils import get_logger


class DbReaderService:
    def __init__(self, app: FastAPI):
        self.app = app
        self._logger = get_logger("db_reader")
        self._setup_routes()

    def _setup_routes(self):
        # Include API routes
        self.app.include_router(database_router)
        self.app.include_router(monitor_router)

    def run(self):
        uvicorn.run("components.db_reader.main:app", host="0.0.0.0", port=8001)
