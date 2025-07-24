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
    result = page_content_extractor.extract(TEST_URL, SAMPLE_HTML)

    assert result.title == "Test Page"
    assert result.categories == ["Category 1", "Category 2"]
    assert result.text_content == "This is the summary paragraph\nThis is the body paragraph"
    assert result.text_content_hash == "fakehash123"

