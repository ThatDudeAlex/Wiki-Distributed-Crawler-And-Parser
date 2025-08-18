"""
Entrypoint for db_reader component.

Initializes the FastAPI app and starts the Uvicorn server via DbReaderService
"""

from fastapi import FastAPI
from prometheus_client import start_http_server
from components.db_reader.services.reader_service import DbReaderService
from shared.configs.config_loader import component_config_loader

COMPONENT_NAME = "db_reader"

app = FastAPI()
configs = component_config_loader(COMPONENT_NAME)

# TODO: add component configs during cleanup
        # If needed put port as part of a component config ()
prometheus_port = 8000
start_http_server(prometheus_port)
service = DbReaderService(app, configs)

if __name__ == "__main__":
    service.run()
