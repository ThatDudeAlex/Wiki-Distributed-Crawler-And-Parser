

import gzip
import logging


class CompressFileHandler:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def load_compressed_html(self, filepath: str) -> str:
        """
        Loads and decompresses gzipped HTML content from a given file path

        :param filepath: path to the compressed .gz file

        :return: Decompressed HTML string
        """
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            html_content = f.read()

        self._logger.info(
            f"Loaded compressed HTML file - filepath: {filepath}")
        return html_content
