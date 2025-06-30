import logging
from shared.queue_service import QueueService


class ParsingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger
        pass

    def run(self, url: str, compressed_path: str):
        self._logger.info('Got Told To Run!')
        pass
