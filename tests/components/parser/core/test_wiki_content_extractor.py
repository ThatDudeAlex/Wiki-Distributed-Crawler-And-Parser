from lxml import html
import pytest
from unittest.mock import Mock, patch
from components.parser.core.wiki_content_extractor import PageContentExtractor
from shared.configs.config_loader import component_config_loader

# Sample HTML mimicking a basic Wikipedia-like structure
SAMPLE_HTML = """
<html>
  <head><title>Test Page</title></head>
  <body>
    <h1 id="firstHeading">Sample Article</h1>
    <div id="mw-normal-catlinks">
      <ul>
        <li><a>Category 1</a></li>
        <li><a>Category 2</a></li>
      </ul>
    </div>
    <div id="mw-content-text">
      <p>This is the summary paragraph</p>
      <p>This is the body paragraph</p>
    </div>
  </body>
</html>
"""

TEST_URL = "http://www.example.com"


@pytest.fixture
def logger():
    return Mock()

@pytest.fixture
def configs():
    return component_config_loader("parser", True)


@pytest.fixture
def page_content_extractor(configs, logger):
    return PageContentExtractor(configs, logger)


@patch("components.parser.core.wiki_content_extractor.create_hash", return_value="fakehash123")
def test_extract_wiki_page_content(mock_hash, page_content_extractor):
    # Act
    result = page_content_extractor.extract(TEST_URL, SAMPLE_HTML)

    # Assert
    assert result.title == "Test Page"
    assert result.categories == ["Category 1", "Category 2"]
    assert result.text_content == "This is the summary paragraph\nThis is the body paragraph"
    assert result.text_content_hash == "fakehash123"


def test_extract_missing_title(page_content_extractor):
    # Setup
    html_no_title = SAMPLE_HTML.replace("<title>Test Page</title>", "")

    # Act
    result = page_content_extractor.extract(TEST_URL, html_no_title)

    # Assert
    assert result.title == "Page is missing title"


def test_extract_missing_categories(page_content_extractor):
    # Setup
    html_no_categories = SAMPLE_HTML.replace('<div id="mw-normal-catlinks">', '<div id="other-div">')

    # Act
    result = page_content_extractor.extract(TEST_URL, html_no_categories)

    # Assert
    assert result.categories == []


def test_extract_missing_main_content(page_content_extractor):
    # Setup
    html_no_main_content = SAMPLE_HTML.replace('<div id="mw-content-text">', '<div id="other-id">')

    # Act
    result = page_content_extractor.extract(TEST_URL, html_no_main_content)

    # Assert
    assert result.text_content is None
    assert result.text_content_hash is None


def test_extract_empty_html(page_content_extractor):
    # Act
    result = page_content_extractor.extract(TEST_URL, "")
    
    # Assert
    assert result.title == "Page is blank - skipped"
    assert result.categories == []
    assert result.text_content is None
    assert result.text_content_hash is None



def test_extract_text_cleanup(page_content_extractor):
    # Setup
    dirty_html = SAMPLE_HTML.replace(
        "This is the body paragraph",
        "   \n   This is the body paragraph\n\n   "
    )

    # Act
    result = page_content_extractor.extract(TEST_URL, dirty_html)

    # Assert
    assert result.text_content == "This is the summary paragraph\nThis is the body paragraph"


def test_extract_title_success(page_content_extractor):
    # Setup
    tree = html.fromstring("<html><head><title>Sample Title</title></head></html>")

    # Act
    result = page_content_extractor._extract_title(tree)

    # Assert
    assert result == "Sample Title"


def test_extract_title_missing(page_content_extractor):
    # Setup
    tree = html.fromstring("<html><head></head></html>")

    # Act
    result = page_content_extractor._extract_title(tree)

    # Assert
    assert result is None


def test_extract_title_exception(page_content_extractor):
    # Setup
    # Force xpath to raise by removing 'title' selector
    page_content_extractor.configs['selectors'].pop('title')
    tree = html.fromstring("<html><head><title>Should Fail</title></head></html>")

    # Act
    result = page_content_extractor._extract_title(tree)

    # Assert
    assert result is None


def test_extract_main_body_content_success(page_content_extractor):
    # Setup
    html_tree = html.fromstring("""
    <html>
        <body>
            <div id="mw-content-text"><p>Hello</p></div>
        </body>
    </html>
    """)

    # Act
    result = page_content_extractor._extract_main_body_content(html_tree)

    # Assert
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].tag == "div"


def test_extract_main_body_content_not_found(page_content_extractor):
    # Setup
    html_tree = html.fromstring("<html><body><div id='unrelated'></div></body></html>")

    # Act
    result = page_content_extractor._extract_main_body_content(html_tree)

    # Assert
    assert result == []


def test_extract_main_body_content_exception(page_content_extractor):
    # Setup
    mock_tree = Mock()
    mock_tree.xpath.side_effect = Exception("Error")

    # # Act
    result = page_content_extractor._extract_main_body_content(mock_tree)

    # Assert
    assert result is None


@patch("components.parser.core.wiki_content_extractor.Document")
def test_extract_clean_text_success(mock_doc, page_content_extractor):
    mock_doc_instance = mock_doc.return_value
    mock_doc_instance.summary.return_value = """
        <div>
            <p>This is a paragraph</p>
            <p>This is another paragraph</p>
        </div>
    """

    result = page_content_extractor._extract_clean_text(SAMPLE_HTML)

    expected = "This is a paragraph\nThis is another paragraph"
    assert result == expected

@patch("components.parser.core.wiki_content_extractor.Document")
def test_extract_clean_text_summary_none(mock_doc, page_content_extractor):
    mock_doc_instance = mock_doc.return_value
    mock_doc_instance.summary.return_value = None

    result = page_content_extractor._extract_clean_text(SAMPLE_HTML)
    assert result is None


@patch("components.parser.core.wiki_content_extractor.Document", side_effect=Exception("Error"))
def test_extract_clean_text_exception(mock_doc, page_content_extractor):
    result = page_content_extractor._extract_clean_text(SAMPLE_HTML)

    assert result is None
    args, _ = page_content_extractor.logger.warning.call_args
    assert "Failed to extract clean text" in args[0]


def test_extract_categories_valid(page_content_extractor):
    sample_html = """
    <html>
        <body>
            <div id="mw-normal-catlinks">
                <ul>
                    <li><a>Category:Science</a></li>
                    <li><a>Category:Technology</a></li>
                    <li><a>General</a></li>
                    <li><a>Categories</a></li>
                </ul>
            </div>
        </body>
    </html>
    """
    tree = html.fromstring(sample_html)
    result = page_content_extractor._extract_categories(tree)

    assert result == ["Science", "Technology", "General"]


def test_extract_categories_missing_div(page_content_extractor):
    html_missing_div = "<html><body><div id='other-div'></div></body></html>"
    tree = html.fromstring(html_missing_div)
    result = page_content_extractor._extract_categories(tree)

    assert result == []


def test_extract_categories_xpath_exception(page_content_extractor, mocker):
    # Break XPath evaluation by passing a non-parsable object
    tree = mocker.Mock()
    tree.xpath.side_effect = Exception("Broken XPath")

    result = page_content_extractor._extract_categories(tree)

    assert result == []
    page_content_extractor.logger.exception.assert_called_once()
    args, _ = page_content_extractor.logger.exception.call_args
    assert "extracting page categories" in args[0]
