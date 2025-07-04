import logging
import functools
import os
import sys
from logging.handlers import RotatingFileHandler

# 1. Formatter — shows context info
FORMATTER = logging.Formatter(
    "[%(asctime)s] %(levelname)-8s %(name)s:%(funcName)s():%(lineno)d - %(message)s"
)

# 2. Log level from ENV or default to INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# 3. Color formatter for dev (this is optional but it helps)
try:
    from colorlog import ColoredFormatter

    COLOR_FORMATTER = ColoredFormatter(
        "%(log_color)s[%(asctime)s] %(levelname)-8s %(name)s:%(funcName)s():%(lineno)d - %(message)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        },
    )
except ImportError:
    COLOR_FORMATTER = FORMATTER


def get_logger(name: str, level: str = LOG_LEVEL) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Avoid duplicate handlers

    logger.setLevel(level)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(COLOR_FORMATTER)
    logger.addHandler(ch)

    """
    Rotating file handler

    IMPORTANT:
        Not using something to limit log file size (like rotating logs) will slowly but surely 
        lead to a catastrophic failure. Trust me, your machine or VM will eventually run 
        out of disk space if you don't.

    REAL EXAMPLE:
        I learned this the hard way. I ran a simple, single-instance crawler for three 
        days straight without rotating logs. My VM completely ran out of disk space and 
        crashed because of all the logs piling up. Don't repeat my mistake!
    """
    if os.getenv("LOG_TO_FILE", "1") == "1":

        # Creates log directory if it doesn't exist
        log_dir = os.getenv("LOG_DIR", "./logs")
        os.makedirs(log_dir, exist_ok=True)

        file_path = os.path.join(log_dir, f"{name}.log")
        fh = RotatingFileHandler(file_path, maxBytes=5_000_000, backupCount=5)
        fh.setFormatter(FORMATTER)
        logger.addHandler(fh)

    return logger


# 4. Reusable decorator (uses module-based logger)
def log_execution(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.info(f"→ Calling {func.__name__}()")
        try:
            result = func(*args, **kwargs)
            logger.info(f"✓ Completed {func.__name__}()")
            return result
        except Exception as e:
            logger.error(f"✗ Error in {func.__name__}(): {e}", exc_info=True)
            raise
    return wrapper
