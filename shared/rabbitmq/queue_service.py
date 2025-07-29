import logging
import pika
import time
import os
import json
from pika.exceptions import AMQPConnectionError
from dotenv import load_dotenv

from shared.configs.config_loader import global_config_loader
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

        global_config = global_config_loader()
        rabbitmq_cfg = global_config["rabbitmq"]
        self._host = rabbitmq_cfg["host"]
        self._port = rabbitmq_cfg["port"]
            
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        self.prefetch_count = prefetch_count

        self._connection = None
        self._channel = None

        self._wait_for_rabbit(queue_names)

    def declare_queue_with_dlq(self, queue_name: str, durable=True, dlq_enabled=True):
        """
        Declares a queue with an optional Dead Letter Queue (DLQ) configuration.

        Args:
            queue_name (str): Name of the primary queue.
            durable (bool): If True, the queue survives broker restarts.
            dlq_enabled (bool): If True, sets up DLX/DLQ for message failures.
        """

        if dlq_enabled:
            dlx_name = f"{queue_name}.dlx"
            dlq_name = f"{queue_name}.dlq"

            # Declare DLX exchange
            self._channel.exchange_declare(exchange=dlx_name, exchange_type='direct', durable=True)
            self._logger.info(f"Declared DLX: {dlx_name}")

            # Declare DLQ
            self._channel.queue_declare(queue=dlq_name, durable=durable)
            self._channel.queue_bind(queue=dlq_name, exchange=dlx_name, routing_key=dlq_name)
            self._logger.info(f"Declared and bound DLQ: {dlq_name} to DLX: {dlx_name}")

            queue_args = {
                "x-dead-letter-exchange": dlx_name,
                "x-dead-letter-routing-key": dlq_name,
            }
        else:
            queue_args = {}
        
        # Declare the main queue
        self._channel.queue_declare(queue=queue_name, durable=durable, arguments=queue_args)
        self._logger.info(f"Declared queue: {queue_name} with DLQ: {dlq_enabled}")


    def _declare_queues(self, names: list[str]):
        for name in names:
            self.declare_queue_with_dlq(queue_name=name, durable=True)


    def _wait_for_rabbit(self, queue_names: list):
        retries = 0
        while retries < self.max_retries:
            try:
                self._logger.debug("Attempting RabbitMQ connection...")
                self._connect()

                self._channel.basic_qos(prefetch_count=self.prefetch_count)
                self._declare_queues(queue_names)

                self._logger.info("Initial RabbitMQ connection established")
                return
            except AMQPConnectionError as e:
                retries += 1
                self._logger.warning(
                    f"RabbitMQ not available yet (retry {retries}/{self.max_retries}): {e}")
                time.sleep(self.retry_interval)

        raise RuntimeError("RabbitMQ not reachable after multiple retries")
    
    def _connect(self):
        if self._connection and not self._connection.is_closed:
            return  # Already connected
        
        try:
            creds = pika.PlainCredentials(
                    os.environ["RABBITMQ_USER"],
                    os.environ["RABBITMQ_PASSWORD"],
                )
            self._connection = pika.BlockingConnection(
                pika.ConnectionParameters(self._host, port=self._port, credentials=creds))
            self._channel = self._connection.channel()

        except Exception as e:
            self._logger.error(f"Failed to connect to RabbitMQ: {e}", exc_info=True)
            raise

    def _ensure_channel_open(self):
        if self._channel is None or self._channel.is_closed:
            self._logger.warning("Channel is closed — reconnecting...")
            self._connect()

    def publish(self, queue_name: str, message: QueueMsgSchemaInterface):
        self._ensure_channel_open()
        
        self._channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        self._logger.debug(f"Message published to {queue_name}: {message}")


    # TODO: remove if not needed
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
