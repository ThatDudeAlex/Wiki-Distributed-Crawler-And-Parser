import pika
import time
import os
import json
from pika.exceptions import AMQPConnectionError
from dotenv import load_dotenv


class QueueService:
    def __init__(self, crawl_queue_name, parse_queue_name, logger, retry_interval=10, max_retries=6):
        load_dotenv()
        self.crawl_queue_name = crawl_queue_name
        self.parse_queue_name = parse_queue_name
        self.logger = logger
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        self.connection = None
        self.channel = None

        self._wait_for_rabbit()

    def _wait_for_rabbit(self):
        retries = 0
        while retries < self.max_retries:
            try:
                self.logger.info("Attempting RabbitMQ connection...")

                creds = pika.PlainCredentials(
                    os.environ["RABBITMQ_USER"],
                    os.environ["RABBITMQ_PASSWORD"],
                )
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters("rabbitmq", port=5672, credentials=creds))
                self.channel = self.connection.channel()
                self.channel.basic_qos(prefetch_count=1)
                self.channel.queue_declare(
                    queue=self.crawl_queue_name, durable=True)
                self.channel.queue_declare(
                    queue=self.parse_queue_name, durable=True)

                self.logger.info("RabbitMQ connection established")
                return
            except AMQPConnectionError as e:
                retries += 1
                self.logger.warning(
                    f"RabbitMQ not available yet (retry {retries}/{self.max_retries}): {e}")
                time.sleep(self.retry_interval)

        raise RuntimeError("RabbitMQ not reachable after multiple retries")

    def publish(self, queue_name, message):
        self.channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        self.logger.debug(f"Message published to {queue_name}: {message}")

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
            self.logger.info("RabbitMQ connection closed.")
