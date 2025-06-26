import pika
import time
import os
import json
from pika.exceptions import AMQPConnectionError
from dotenv import load_dotenv


class QueueService:
    def __init__(self, crawl_queue_name, parse_queue_name, logger, retry_interval=10, max_retries=6):
        load_dotenv()
        self._crawl_queue_name = crawl_queue_name
        self._parse_queue_name = parse_queue_name
        self._logger = logger
        self._retry_interval = retry_interval
        self._max_retries = max_retries
        self._connection = None
        self.channel = None

        self._wait_for_rabbit()

    # TODO: test if using this method is better than doing it from directly from the parent class
    # def configure_basic_consume(self, queue_name, callback_function, auto_ack):
    #     self.channel.basic_consume(
    #         queue=queue_name,
    #         on_message_callback=callback_function,
    #         auto_ack=auto_ack
    #     )
    #     return

    def _wait_for_rabbit(self):
        retries = 0
        while retries < self._max_retries:
            try:
                self._logger.info("Attempting RabbitMQ connection...")

                creds = pika.PlainCredentials(
                    os.environ["RABBITMQ_USER"],
                    os.environ["RABBITMQ_PASSWORD"],
                )
                self._connection = pika.BlockingConnection(
                    pika.ConnectionParameters("rabbitmq", port=5672, credentials=creds))
                self.channel = self._connection.channel()
                self.channel.basic_qos(prefetch_count=1)
                self.channel.queue_declare(
                    queue=self._crawl_queue_name, durable=True)
                self.channel.queue_declare(
                    queue=self._parse_queue_name, durable=True)

                self._logger.info("RabbitMQ connection established")
                return
            except AMQPConnectionError as e:
                retries += 1
                self._logger.warning(
                    f"RabbitMQ not available yet (retry {retries}/{self._max_retries}): {e}")
                time.sleep(self._retry_interval)

        raise RuntimeError("RabbitMQ not reachable after multiple retries")

    def publish(self, queue_name, message):
        self.channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        self._logger.debug(f"Message published to {queue_name}: {message}")

    def close(self):
        if self._connection and self._connection.is_open:
            self._connection.close()
            self._logger.info("RabbitMQ connection closed.")
