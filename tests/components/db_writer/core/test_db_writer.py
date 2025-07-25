import logging
from unittest.mock import Mock
import pytest
from components.db_writer.core.db_writer import _get_or_create_categories, add_links_to_schedule, save_page_metadata, save_parsed_data, save_processed_links
from shared.rabbitmq.schemas.save_to_db import CrawlTask, SaveLinksToSchedule, SavePageMetadataTask, SaveParsedContent, SaveProcessedLinks
from shared.rabbitmq.enums.crawl_status import CrawlStatus
from shared.rabbitmq.schemas.scheduling import LinkData
from database.db_models.models import Category


@pytest.fixture
def valid_page_metadata():
    return SavePageMetadataTask(
        status=CrawlStatus.SUCCESS,
        fetched_at="2025-07-24T12:00:00",
        url="https://example.com",
        http_status_code=200,
        url_hash="hash1",
        html_content_hash="hash2",
        compressed_filepath="/path/to/file",
        next_crawl="2025-07-30T12:00:00",
        error_type=None,
        error_message=None
    )

@pytest.fixture
def mock_db_context(mocker):
    mock_db = mocker.Mock()
    mock_context = mocker.MagicMock()
    mock_context.__enter__.return_value = mock_db
    mock_context.__exit__.return_value = None

    mocker.patch(
        "components.db_writer.core.db_writer.get_db",
        return_value=mock_context
    )
    return mock_db

@pytest.fixture
def mock_logger():
    return Mock(spec=logging.Logger)


def test_save_page_metadata_success(valid_page_metadata, mock_logger, mock_db_context, mocker):
    # Setup
    mock_db = mocker.Mock()
    mock_session_factory = mocker.Mock(return_value=mock_db)

    # Act
    save_page_metadata(valid_page_metadata, mock_logger, session_factory=mock_session_factory)

    # Assert
    mock_db_context.execute.assert_called_once()


def test_save_page_metadata_failure(mock_db_context, mock_logger, valid_page_metadata):
    # Setup
    # Simulate a DB error
    mock_db_context.execute.side_effect = RuntimeError("Simulated DB failure")

    # Act
    save_page_metadata(valid_page_metadata, mock_logger)

    # Assert
    mock_logger.error.assert_called_once()
    args, _ = mock_logger.error.call_args
    assert valid_page_metadata.url in args[1]


def test_save_processed_links_success(mock_db_context, mock_logger):
    # Setup
    link = LinkData(
        source_page_url="https://example.com",
        url="https://example.com/about",
        depth=1,
        discovered_at="2025-07-24T12:00:00",
        is_internal=True,
        anchor_text="About Us",
        title_attribute="About",
        rel_attribute="nofollow",
        id_attribute="about-link",
        link_type="internal"
    )

    processed_links = SaveProcessedLinks(links=[link])

    # Act
    save_processed_links(processed_links, mock_logger)

    # Assert
    mock_db_context.execute.assert_called_once()


def test_save_processed_links_empty_list_skips_insert(mock_db_context, mock_logger):
    # Setup
    processed_links = SaveProcessedLinks(links=[])

    # Act
    save_processed_links(processed_links, mock_logger)

    # Assert
    mock_db_context.execute.assert_not_called()


def test_save_parsed_data_inserts_new_page(mock_db_context, mocker, mock_logger):
    # Setup
    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.first.return_value = None
    mock_db_context.query.return_value = mock_query

    category_1 = Category(name="cat1")
    category_2 = Category(name="cat2")

    mocker.patch(
        "components.db_writer.core.db_writer._get_or_create_categories",
        return_value=[category_1, category_2]
    )

    page_data = SaveParsedContent(
        source_page_url="https://example.com/page",
        title="Title",
        parsed_at="2025-07-24T12:00:00",
        text_content="content",
        text_content_hash="abc123",
        categories=["cat1", "cat2"]
    )

    result = save_parsed_data(page_data, mock_logger)

    mock_db_context.add.assert_called_once()
    assert result is True


def test_save_parsed_data_updates_existing_page(mock_db_context, mocker, mock_logger):
    # Setup
    existing_page = mocker.Mock()

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.first.return_value = existing_page
    mock_db_context.query.return_value = mock_query

    category_1 = Category(name="cat1")
    category_2 = Category(name="cat2")

    mocker.patch(
        "components.db_writer.core.db_writer._get_or_create_categories",
        return_value=[category_1, category_2]
    )

    page_data = SaveParsedContent(
        source_page_url="https://example.com/page",
        title="Updated Title",
        parsed_at="2025-07-24T12:00:00",
        text_content="Updated Content",
        text_content_hash="updatedhash123",
        categories=["cat1", "cat2"]
    )

    result = save_parsed_data(page_data, mock_logger)

    assert existing_page.title == page_data.title
    assert existing_page.text_content == page_data.text_content
    assert existing_page.text_content_hash == page_data.text_content_hash
    assert existing_page.parsed_at == page_data.parsed_at
    assert existing_page.categories == [category_1, category_2]
    assert result is True


def test_save_parsed_data_handles_exception(mock_db_context, mock_logger):
    mock_db_context.query.side_effect = RuntimeError("Simulated failure")

    page_data = SaveParsedContent(
        source_page_url="https://example.com/page",
        title="Title",
        parsed_at="2025-07-24T12:00:00",
        text_content="content",
        text_content_hash="abc123",
        categories=["cat1"]
    )

    result = save_parsed_data(page_data, mock_logger)

    assert result is False


def test_add_links_to_schedule_success(mock_db_context, mock_logger):
    links = [
        CrawlTask(
            url="https://example.com",
            depth=1,
            scheduled_at="2025-07-24T12:00:00"
        ),
        CrawlTask(
            url="https://example.org",
            depth=2,
            scheduled_at="2025-07-24T13:00:00"
        )
    ]

    data = SaveLinksToSchedule(links=links)

    add_links_to_schedule(data, mock_logger)

    mock_db_context.execute.assert_called_once()


def test_add_links_to_schedule_skips_on_empty(mock_db_context, mock_logger):
    data = SaveLinksToSchedule(links=[])

    add_links_to_schedule(data, mock_logger)

    mock_db_context.execute.assert_not_called()


def test_add_links_to_schedule_raises_on_failure(mock_db_context, mock_logger):
    mock_db_context.execute.side_effect = RuntimeError("DB write failed")

    links = [
        CrawlTask(
            url="https://example.com",
            depth=0,
            scheduled_at="2025-07-24T12:00:00"
        )
    ]
    data = SaveLinksToSchedule(links=links)

    with pytest.raises(RuntimeError, match="DB write failed"):
        add_links_to_schedule(data, mock_logger)


def test_get_or_create_categories_all_exist(mocker):
    db = mocker.Mock()

    existing = [Category(name="cat1"), Category(name="cat2")]
    query_mock = mocker.Mock()
    query_mock.filter.return_value.all.return_value = existing
    db.query.return_value = query_mock

    result = _get_or_create_categories(db, ["cat1", "cat2"])

    db.add_all.assert_called_once_with([])
    db.flush.assert_called_once()
    assert result == existing


def test_get_or_create_categories_some_new(mocker):
    # Setup
    db = mocker.Mock()

    existing = [Category(name="cat1")]
    query_mock = mocker.Mock()
    query_mock.filter.return_value.all.return_value = existing
    db.query.return_value = query_mock

    # Act
    result = _get_or_create_categories(db, ["cat1", "cat2"])

    # Assert
    db.add_all.assert_called_once()
    db.flush.assert_called_once()

    created = db.add_all.call_args[0][0]
    assert any(c.name == "cat2" for c in created)
    assert len(result) == 2


def test_get_or_create_categories_all_new(mocker):
    db = mocker.Mock()

    query_mock = mocker.Mock()
    query_mock.filter.return_value.all.return_value = []
    db.query.return_value = query_mock

    result = _get_or_create_categories(db, ["cat1", "cat2"])

    db.add_all.assert_called_once()
    db.flush.assert_called_once()
    created = db.add_all.call_args[0][0]

    assert all(isinstance(c, Category) for c in created)
    assert {c.name for c in created} == {"cat1", "cat2"}
    assert len(result) == 2

