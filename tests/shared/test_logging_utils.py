import re
import pytest
from shared.logging_utils import get_logger

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")

def _strip_ansi(s: str) -> str:
    return ANSI_ESCAPE_RE.sub("", s)

def successful_function(a, b):
    logger = get_logger(__name__)
    logger.info("adding %s + %s", a, b)
    return a + b

def failing_function():
    logger = get_logger(__name__)
    logger.error("about to raise ValueError")
    raise ValueError("This is a test error")


def test_successful_function_logs(caplog):
    with caplog.at_level("INFO"):
        result = successful_function(3, 4)

    assert result == 7

    # Ensure our message appeared
    assert any("adding 3 + 4" in msg for msg in caplog.messages)

    # Ensure there's at least one INFO record
    assert any(r.levelname == "INFO" for r in caplog.records)


def test_failing_function_logs_exception(caplog):
    with caplog.at_level("INFO"):
        with pytest.raises(ValueError, match="This is a test error"):
            failing_function()

    # Ensure our error log appeared
    assert any("about to raise ValueError" in msg for msg in caplog.messages)

    # Ensure there's at least one ERROR record
    assert any(r.levelname == "ERROR" for r in caplog.records)


def test_get_logger_returns_same_instance():
    logger1 = get_logger("my.module")
    logger2 = get_logger("my.module")
    assert logger1 is logger2  # Same instance, no duplicate handlers
