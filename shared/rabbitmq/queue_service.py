import logging
import pika
import time
import os
import json
from pika.exceptions import AMQPConnectionError
from dotenv import load_dotenv

from shared.rabbitmq.types import QueueMsgSchemaInterface


class QueueService:
    def __init__(
        self,
        logger: logging.Logger,
        queue_names: list,
        retry_interval: int = 10,
        max_retries: int = 6
    ):
        load_dotenv()
        self._logger = logger
        self._retry_interval = retry_interval
        self._max_retries = max_retries
        self._connection = None
        self.channel = None

        self._wait_for_rabbit(queue_names)

    def _declare_queues(self, names: list[str]):
        for name in names:
            self.channel.queue_declare(queue=name, durable=True)

    def _wait_for_rabbit(self, queue_names: list):
        retries = 0
        while retries < self._max_retries:
            try:
                self._logger.debug("Attempting RabbitMQ connection...")

                creds = pika.PlainCredentials(
                    os.environ["RABBITMQ_USER"],
                    os.environ["RABBITMQ_PASSWORD"],
                )
                self._connection = pika.BlockingConnection(
                    pika.ConnectionParameters("rabbitmq", port=5672, credentials=creds))
                self.channel = self._connection.channel()
                self.channel.basic_qos(prefetch_count=1)
                self._declare_queues(queue_names)

                self._logger.info("RabbitMQ connection established")
                return
            except AMQPConnectionError as e:
                retries += 1
                self._logger.warning(
                    f"RabbitMQ not available yet (retry {retries}/{self._max_retries}): {e}")
                time.sleep(self._retry_interval)

        raise RuntimeError("RabbitMQ not reachable after multiple retries")

    def publish(self, queue_name: str, message: QueueMsgSchemaInterface):
        self.channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=json.dumps(message.to_dict()),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        self._logger.debug(f"Message published to {queue_name}: {message}")

    def close(self):
        if self._connection and self._connection.is_open:
            self._connection.close()
            self._logger.info("RabbitMQ connection closed")
