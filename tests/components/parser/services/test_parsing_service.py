import pytest
from unittest.mock import Mock, patch
from components.parser.services.parsing_service import ParsingService
from shared.configs.config_loader import component_config_loader
from shared.rabbitmq.schemas.parsing import ParsingTask


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def mock_queue_service():
    return Mock()


@pytest.fixture
def configs():
    return component_config_loader("parser", True)


@pytest.fixture
def parsing_service(configs, mock_queue_service, mock_logger):
    service = ParsingService(
        configs=configs,
        queue_service=mock_queue_service,
        logger=mock_logger
    )
    service.content_extractor = Mock()
    service.link_extractor = Mock()
    service._publisher = Mock()
    return service


@pytest.fixture
def sample_task():
    return ParsingTask(
        url="http://example.com",
        depth=1,
        compressed_filepath="/fake/path/page.html.gz"
    )


@patch("components.parser.services.parsing_service.load_compressed_html")
@patch("components.parser.services.parsing_service.STAGE_DURATION_SECONDS")
@patch("components.parser.services.parsing_service.LINKS_EXTRACTED_TOTAL")
@patch("components.parser.services.parsing_service.PAGES_PARSED_TOTAL")
def test_run_success(
    mock_pages_parsed,
    mock_links_total,
    mock_stage_duration,
    mock_load_html,
    parsing_service,
    sample_task
):
    # Setup
    mock_html = "<html>fake</html>"
    mock_load_html.return_value = mock_html
    parsing_service.content_extractor.extract.return_value = Mock()
    parsing_service.link_extractor.extract.return_value = [Mock(), Mock()]

    # Act
    parsing_service.run(sample_task)

    # # Assert
    mock_load_html.assert_called_once_with(sample_task.compressed_filepath, parsing_service._logger)
    parsing_service.content_extractor.extract.assert_called_once_with(sample_task.url, mock_html)
    parsing_service.link_extractor.extract.assert_called_once_with(sample_task.url, mock_html, sample_task.depth)
    parsing_service._publisher.publish_save_parsed_data.assert_called_once()
    parsing_service._publisher.publish_process_links_task.assert_called_once()
    mock_links_total.inc.assert_called_once_with(2)
    mock_pages_parsed.inc.assert_called_once()


@patch("components.parser.services.parsing_service.load_compressed_html", return_value=None)
@patch("components.parser.services.parsing_service.PAGES_PARSED_TOTAL")
def test_run_skips_when_html_is_none(mock_pages_parsed, mock_load_html, parsing_service, sample_task):
    # Act
    parsing_service.run(sample_task)

    # Assert
    parsing_service._logger.error.assert_called_with(
        "Skipping Parsing Task - HTML content could not be loaded"
    )
    mock_pages_parsed.inc.assert_called_once()


@patch("components.parser.services.parsing_service.load_compressed_html")
@patch("components.parser.services.parsing_service.PAGES_PARSED_TOTAL")
def test_run_handles_unexpected_exception(mock_pages_parsed, mock_load_html, parsing_service, sample_task):
    # Simulate exception during content extraction
    mock_load_html.return_value = "<html>ok</html>"
    parsing_service.content_extractor.extract.side_effect = Exception("error")

    # Act
    parsing_service.run(sample_task)

    # # Assert
    parsing_service._logger.exception.assert_called_once_with(
        "Unexpected error during parsing task for %s", sample_task.url
    )
    mock_pages_parsed.inc.assert_called_once()
