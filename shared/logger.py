import logging
import os

# TODO: Move into my own python-utilities package


def setup_logging(file_path: str) -> logging.Logger:
    """
    Sets up & returns a logger with handlers for both the console 
    and the file in `file_path`
    """

    # Creates log directory if it doesn't exist
    log_dir = os.path.dirname(file_path)
    os.makedirs(log_dir, exist_ok=True)

    # Initiate logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter_c = logging.Formatter('%(levelname)s - %(message)s')

    console_handler.setFormatter(formatter_c)
    logger.addHandler(console_handler)

    # File handler
    try:
        file_handler = logging.FileHandler(file_path)

        # Log only warning & up into file
        file_handler.setLevel(logging.WARNING)
        formatter_f = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s\n')
        file_handler.setFormatter(formatter_f)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f'Error creating logger file handler: {e}')

    return logger
