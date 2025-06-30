import unittest
from unittest.mock import Mock, patch
import json
import logging

from components.db_writer.message_handler import handle_save_page_message, handle_save_parsed_content_message


class TestMessageHandlers(unittest.TestCase):
    def setUp(self):
        self.logger = Mock(spec=logging.Logger)
        self.ch = Mock()
        self.method = Mock()
        self.method.delivery_tag = 'test_tag'
        self.properties = Mock()

    @patch('components.db_writer.message_handler.save_crawled_page')
    def test_handle_save_page_message_success(self, mock_save):
        body = json.dumps({"url": "http://example.com"}).encode()
        handle_save_page_message(self.ch, self.method,
                                 self.properties, body, self.logger)

        mock_save.assert_called_once()
        self.ch.basic_ack.assert_called_with(delivery_tag='test_tag')
        self.ch.basic_nack.assert_not_called()

    @patch('components.db_writer.message_handler.save_crawled_page')
    def test_handle_save_page_message_value_error(self, mock_save):
        body = b'invalid_json'
        handle_save_page_message(self.ch, self.method,
                                 self.properties, body, self.logger)

        mock_save.assert_not_called()
        self.ch.basic_nack.assert_called_once_with(
            delivery_tag='test_tag', requeue=False)
        self.ch.basic_ack.assert_not_called()

    @patch('components.db_writer.message_handler.save_crawled_page', side_effect=Exception("DB error"))
    def test_handle_save_page_message_generic_exception(self, mock_save):
        body = json.dumps({"url": "http://example.com"}).encode()
        handle_save_page_message(self.ch, self.method,
                                 self.properties, body, self.logger)

        self.ch.basic_nack.assert_called_once_with(
            delivery_tag='test_tag', requeue=False)
        self.ch.basic_ack.assert_not_called()

    @patch('components.db_writer.message_handler.save_parsed_page_content')
    def test_handle_save_parsed_content_message_success(self, mock_save):
        body = json.dumps({"content": "some data"}).encode()
        handle_save_parsed_content_message(
            self.ch, self.method, self.properties, body, self.logger)

        mock_save.assert_called_once()
        self.ch.basic_ack.assert_called_with(delivery_tag='test_tag')

    @patch('components.db_writer.message_handler.save_parsed_page_content')
    def test_handle_save_parsed_content_message_value_error(self, mock_save):
        body = b'invalid_json'
        handle_save_parsed_content_message(
            self.ch, self.method, self.properties, body, self.logger)

        mock_save.assert_not_called()
        self.ch.basic_nack.assert_called_with(
            delivery_tag='test_tag', requeue=False)

    @patch('components.db_writer.message_handler.save_parsed_page_content', side_effect=Exception("Some failure"))
    def test_handle_save_parsed_content_message_generic_exception(self, mock_save):
        body = json.dumps({"content": "some data"}).encode()
        handle_save_parsed_content_message(
            self.ch, self.method, self.properties, body, self.logger)

        self.ch.basic_nack.assert_called_with(
            delivery_tag='test_tag', requeue=False)
        self.ch.basic_ack.assert_not_called()
