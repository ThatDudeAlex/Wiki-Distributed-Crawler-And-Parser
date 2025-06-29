import re
import pytest
from shared.logging_utils import log_execution, get_logger


@log_execution
def successful_function(x, y):
    return x + y


@log_execution
def failing_function():
    raise ValueError("This is a test error")


def test_successful_function_logs(caplog):
    with caplog.at_level("INFO"):
        result = successful_function(3, 4)

    assert result == 7
    assert any("→ Calling successful_function()" in msg for msg in caplog.messages)
    assert any(
        "✓ Completed successful_function()" in msg for msg in caplog.messages)


def test_failing_function_logs_exception(caplog):
    with caplog.at_level("INFO"):
        with pytest.raises(ValueError, match="This is a test error"):
            failing_function()

    assert any("→ Calling failing_function()" in msg for msg in caplog.messages)
    assert any(
        "✗ Error in failing_function(): This is a test error" in msg for msg in caplog.messages)


def test_get_logger_returns_same_instance():
    logger1 = get_logger("my.module")
    logger2 = get_logger("my.module")
    assert logger1 is logger2  # Same instance, no duplicate handlers


def test_log_output_format(caplog):
    with caplog.at_level("INFO"):
        successful_function(1, 1)

    # Regex to match: `LEVEL name:filename.py:line msg``
    log_pattern = re.compile(
        # log level padded
        r"(INFO|ERROR|WARNING|DEBUG|CRITICAL)\s{1,8}"
        # name:filename.py:line
        r"[a-zA-Z0-9_.]+:[a-zA-Z0-9_./\\]+\.py:\d+ "
        # message
        r".+"
    )

    log_lines = caplog.text.strip().splitlines()
    for line in log_lines:
        assert log_pattern.match(
            line), f"Log line doesn't match expected format: {line}"
