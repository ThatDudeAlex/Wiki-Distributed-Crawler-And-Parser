import logging
from pathlib import Path
import pika
import time
import os
import json
from pika.exceptions import AMQPConnectionError
from dotenv import load_dotenv

from shared.configs.config_loader import config_loader
from shared.rabbitmq.types import QueueMsgSchemaInterface

load_dotenv()

class QueueService:
    def __init__(
        self,
        logger: logging.Logger,
        queue_names: list,
        retry_interval: int = 10,
        max_retries: int = 6,
        prefetch_count: int = 1
    ):
        self._logger = logger

        config_path = Path(__file__).resolve().parents[1] / "configs" / "global_config.yml"
        global_config = config_loader(config_path)
        rabbitmq_cfg = global_config["rabbitmq"]
        self._host = rabbitmq_cfg["host"]
        self._port = rabbitmq_cfg["port"]
    
        # logger.info('rabbitmq_cfg: %s', rabbitmq_cfg)
        
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        self.prefetch_count = prefetch_count

        self._connection = None
        self._channel = None

        self._wait_for_rabbit(queue_names)

    def _declare_queues(self, names: list[str]):
        for name in names:
            self._channel.queue_declare(queue=name, durable=True)

    def _wait_for_rabbit(self, queue_names: list):
        retries = 0
        while retries < self.max_retries:
            try:
                self._logger.debug("Attempting RabbitMQ connection...")

                creds = pika.PlainCredentials(
                    os.environ["RABBITMQ_USER"],
                    os.environ["RABBITMQ_PASSWORD"],
                )
                self._connection = pika.BlockingConnection(
                    pika.ConnectionParameters(self._host, port=self._port, credentials=creds))
                self._channel = self._connection.channel()
                self._channel.basic_qos(prefetch_count=self.prefetch_count)
                self._declare_queues(queue_names)

                self._logger.info("RabbitMQ connection established")
                return
            except AMQPConnectionError as e:
                retries += 1
                self._logger.warning(
                    f"RabbitMQ not available yet (retry {retries}/{self.max_retries}): {e}")
                time.sleep(self.retry_interval)

        raise RuntimeError("RabbitMQ not reachable after multiple retries")

    def publish(self, queue_name: str, message: QueueMsgSchemaInterface):
        self._channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            # body=json.dumps(message.to_dict()),
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        self._logger.debug(f"Message published to {queue_name}: {message}")

    def setup_delay_queue(self, delay_queue_name: str, processing_queue_name: str, exchange: str = ''):
        """
        Declare a delay queue with dead-letter routing and fixed TTL for rate limiting.

        Args:
            delay_queue_name (str): Name of the delay queue to create.
            processing_queue_name (str): Queue to route messages to after delay.
            exchange (str, optional): DLX to route to; '' = default exchange.
        """
        arguments = {
            'x-dead-letter-exchange': exchange,
            'x-dead-letter-routing-key': processing_queue_name,
        }

        self._channel.queue_declare(
            queue=delay_queue_name,
            durable=True,
            arguments=arguments
        )

    def publish_with_ttl(self, queue_name: str, message: QueueMsgSchemaInterface, ttl_ms: int):
        properties = pika.BasicProperties(expiration=str(ttl_ms))
        self._channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message.to_dict()),
            properties=properties
        )
        self._logger.debug(f"TTL Message published to {queue_name}: {message}")

    def close(self):
        if self._connection and self._connection.is_open:
            self._connection.close()
            self._logger.info("RabbitMQ connection closed")
