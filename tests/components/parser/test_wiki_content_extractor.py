import pytest
from unittest.mock import Mock, patch
from components.parser.configs.parser_config import configs as loaded_configs
from components.parser.core.wiki_content_extractor import PageContentExtractor

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
def page_content_extractor(logger):
    return PageContentExtractor(loaded_configs.selectors, logger)


@patch("components.parser.core.wiki_content_extractor.create_hash", return_value="fakehash123")
@patch("components.parser.core.wiki_content_extractor.clean_wiki_html_content", return_value="Cleaned content")
def test_extract_wiki_page_content(mock_clean, mock_hash, page_content_extractor):
    result = page_content_extractor.extract(TEST_URL, SAMPLE_HTML)

    assert result.title == "Test Page"
    assert result.categories == ["Category 1", "Category 2"]
    assert result.summary == "This is the summary paragraph"
    assert result.text_content == "Cleaned content"
    assert result.text_content_hash == "fakehash123"


@patch("components.parser.core.wiki_content_extractor.create_hash")
@patch("components.parser.core.wiki_content_extractor.clean_wiki_html_content")
def test_no_main_content(mock_clean, mock_hash, page_content_extractor):
    html = "<html><body><h1 id='firstHeading'>Title</h1></body></html>"
    result = page_content_extractor.extract(TEST_URL, html)

    assert result.summary is None
    assert result.text_content is None
    assert result.text_content_hash is None


@patch("components.parser.core.wiki_content_extractor.clean_wiki_html_content")
@patch("components.parser.core.wiki_content_extractor.create_hash")
def test_no_categories(mock_hash, mock_clean, page_content_extractor):
    html = """
    <html>
        <h1 id="firstHeading">Test Page</h1>
        <div id="mw-content-text">
            <p>Summary paragraph</p>
            <p>Body paragraph</p>
        </div>
    </html>
    """

    mock_soup = Mock()
    mock_soup.get_text.return_value = "Cleaned content"
    mock_clean.return_value = mock_soup
    mock_hash.return_value = "mocked_hash_string"

    result = page_content_extractor.extract(TEST_URL, html)

    assert result.categories == []
    assert result.text_content_hash == "mocked_hash_string"


@patch("components.parser.core.wiki_content_extractor.create_hash", return_value="hash123")
# @patch("components.parser.core.wiki_content_extractor.summary", return_value="Only paragraph available")
def test_single_paragraph_summary(mock_hash, page_content_extractor):
    html = """
    <html>
        <h1 id="firstHeading">Only Title</h1>
        <div id="mw-content-text">
            <p>Only paragraph available</p>
        </div>
    </html>
    """

    result = page_content_extractor.extract(TEST_URL, html)

    assert result.summary == "Only paragraph available"
    assert result.text_content == "Only paragraph available"
    assert result.text_content_hash == "hash123"
