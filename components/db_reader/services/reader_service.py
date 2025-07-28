
from typing import Any
from fastapi import FastAPI
import uvicorn
from components.db_reader.api.database_routes import database_router
from components.db_reader.api.monitoring_routes import monitor_router
from shared.logging_utils import get_logger


class DbReaderService:
    """
    Service responsible for configuring and running the db_reader FastAPI application
    """

    def __init__(self, app: FastAPI, configs: dict[str, Any]):
        self._host = configs['network']['host']
        self._port = configs['network']['port']

        self._logger = get_logger(
            configs['logging']['logger_name'], configs['logging']['log_level']
        )
        
        self.app = app
        self._setup_routes()

    def _setup_routes(self):
        """
        Include all relevant routers in the FastAPI app
        """
        # Include API routes
        self.app.include_router(database_router)
        self.app.include_router(monitor_router)

    def run(self):
        """
        Start the FastAPI server using uvicorn
        """
        self._logger.info("Running Db_Reader Component...")
        uvicorn.run(self.app, host=self._host, port=self._port)
