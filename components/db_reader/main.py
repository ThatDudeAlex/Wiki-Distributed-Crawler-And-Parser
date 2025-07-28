"""
Entrypoint for db_reader component.

Initializes the FastAPI app and starts the Uvicorn server via DbReaderService
"""

from fastapi import FastAPI
from components.db_reader.services.reader_service import DbReaderService
from shared.configs.config_loader import component_config_loader

COMPONENT_NAME = "db_reader"

app = FastAPI()
configs = component_config_loader(COMPONENT_NAME)
service = DbReaderService(app, configs)

if __name__ == "__main__":
    service.run()
