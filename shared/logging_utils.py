import logging
import sys

# TODO: Implement structured logs with structlog

# 1. Formatter — shows context info
FORMATTER = logging.Formatter(
    "[%(asctime)s] %(levelname)-8s %(name)s:%(funcName)s():%(lineno)d - %(message)s"
)

# 2. Log level from ENV or default to INFO
DEFAULT_LOG_LEVEL = "INFO"

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


def get_logger(name: str, level: str = DEFAULT_LOG_LEVEL) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Avoid duplicate handlers

    logger.setLevel(level)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(COLOR_FORMATTER)
    logger.addHandler(ch)

    return logger


