import unittest
import tempfile
import gzip
import os
import logging
from io import StringIO
from components.parser.services.compressed_html_reader import load_compressed_html


class TestLoadCompressedHTML(unittest.TestCase):
    def setUp(self):

        # Create a logger that writes to a string buffer (to avoid real logging output)
        self.log_stream = StringIO()
        self.logger = logging.getLogger("test_logger")
        handler = logging.StreamHandler(self.log_stream)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        self.addCleanup(self.logger.removeHandler, handler)

        # Create a temporary gzipped HTML file
        self.test_html = "<html><body><h1>Hello, world!</h1></body></html>"
        self.temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix='.gz')
        with gzip.open(self.temp_file.name, 'wt', encoding='utf-8') as f:
            f.write(self.test_html)

    def tearDown(self):
        os.remove(self.temp_file.name)

    def test_load_compressed_html(self):
        result = load_compressed_html(self.temp_file.name, self.logger)
        self.assertEqual(result, self.test_html)

        # Check if the logger captured the correct log
        self.log_stream.seek(0)
        log_contents = self.log_stream.read()
        self.assertIn("Loaded compressed HTML file in filepath", log_contents)
        self.assertIn(self.temp_file.name, log_contents)


if __name__ == '__main__':
    unittest.main()
