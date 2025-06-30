

import gzip
import logging


def load_compressed_html(filepath: str, logger: logging.Logger) -> str:
    """
    Loads and decompresses gzipped HTML content from a given file path

    :param filepath: path to the compressed .gz file

    :return: Decompressed HTML string
    """

    # TODO: Investigate if a `Retry Mechanism` would help here
    try:
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            html_content = f.read()

        logger.info(f"Loaded compressed HTML file in filepath: {filepath}")
        return html_content
    except Exception as e:
        exception_type_name = type(e).__name__
        logger.error(
            f"An exception of type '{exception_type_name}' occurred: {e}")
        return None
