import re
from unittest.mock import Mock, patch

from lxml import html
import pytest
from components.parser.core.wiki_link_extractor import PageLinkExtractor
from shared.configs.config_loader import component_config_loader
from shared.rabbitmq.schemas.scheduling import LinkData


@pytest.fixture
def logger():
    return Mock()

@pytest.fixture
def configs():
    return component_config_loader("parser", True)

@pytest.fixture
def link_extractor(configs, logger):
    return PageLinkExtractor(configs, logger)


@pytest.fixture
def content_id(configs):
    id_selector = configs['selectors']['content_container_id']
    match = re.search(r'id="([^"]+)"', id_selector)
    return match.group(1)


@patch.object(PageLinkExtractor, "normalize_url", return_value="http://example.com/wiki/Test_Page")
@patch.object(PageLinkExtractor, "is_internal_link", return_value=True)
@patch.object(PageLinkExtractor, "_determine_type", return_value="wikilink")
@patch("components.parser.core.wiki_link_extractor.get_timestamp_eastern_time", return_value="2025-07-24T12:00:00")
def test_build_link_data_valid(mock_time, mock_type, mock_internal, mock_norm, link_extractor):
    sample_html = '<a href="/wiki/Test_Page" rel="nofollow" title="Test Page" id="link1">Link Text</a>'
    element = html.fromstring(sample_html)

    result = link_extractor._build_link_data(element, "http://example.com", 2)

    assert isinstance(result, LinkData)
    assert result.url == "http://example.com/wiki/Test_Page"
    assert result.anchor_text == "Link Text"
    assert result.title_attribute == "Test Page"
    assert result.rel_attribute == "nofollow"
    assert result.id_attribute == "link1"
    assert result.link_type == "wikilink"
    assert result.depth == 3
    assert result.discovered_at == "2025-07-24T12:00:00"
    assert result.is_internal is True


@patch.object(PageLinkExtractor, "_build_link_data")
def test_extract_valid_links(mock_build, link_extractor):
    mock_build.return_value = LinkData(
        source_page_url="http://example.com",
        url="http://example.com/wiki/Link",
        depth=2,
        discovered_at="2025-07-24T12:00:00",
        anchor_text="Link",
        title_attribute="",
        rel_attribute="",
        id_attribute="",
        link_type="wikilink",
        is_internal=True
    )

    html_content = """
    <html><body>
        <div id="mw-content-text">
            <a href="/wiki/Link">Link</a>
        </div>
    </body></html>
    """

    results = link_extractor.extract("http://example.com", html_content, depth=1)

    assert len(results) == 1
    assert results[0].url == "http://example.com/wiki/Link"


def test_extract_no_main_content(link_extractor):
    html_content = """
    <html><body>
        <div id="other-id">
            <a href="/wiki/Link">Link</a>
        </div>
    </body></html>
    """

    results = link_extractor.extract("http://example.com", html_content, depth=0)

    assert results == []
    link_extractor.logger.warning.assert_called_with(
        "No main content found: %s", "http://example.com"
    )


@patch.object(PageLinkExtractor, "_build_link_data", return_value=None)
def test_extract_no_valid_links(mock_build, link_extractor):
    html_content = """
    <html><body>
        <div id="mw-content-text">
            <a href="/wiki/Link">Link</a>
        </div>
    </body></html>
    """

    results = link_extractor.extract("http://example.com", html_content, depth=1)

    assert results == []
    link_extractor.logger.warning.assert_called_with(
        "No valid links found: %s", "http://example.com"
    )


def test_build_link_data_missing_href(link_extractor):
    html_snippet = '<a title="No href">No link</a>'
    element = html.fromstring(html_snippet)

    result = link_extractor._build_link_data(element, "http://example.com", 1)

    assert result is None


@patch.object(PageLinkExtractor, "normalize_url", side_effect=Exception("Fail"))
def test_build_link_data_exception(mock_norm, link_extractor):
    html_snippet = '<a href="/wiki/Fail">Bad Link</a>'
    element = html.fromstring(html_snippet)

    result = link_extractor._build_link_data(element, "http://example.com", 0)

    assert result is None


def test_determine_type_internal_link(link_extractor, content_id):
    html = f'''<div id="{content_id}"><a href="/wiki/Python_(programming_language)">Python</a></div>'''
    links = link_extractor.extract(
        'https://en.wikipedia.org/wiki/Main_Page', html, 0)
    assert len(links) == 1
    assert links[0].link_type == 'wikilink'


def test_determine_type_external_link(link_extractor, content_id):
    html = f'''<div id="{content_id}"><a href="http://example.com">Example</a></div>'''
    links = link_extractor.extract(
        'https://en.wikipedia.org/wiki/Main_Page', html, 1
    )
    assert links[0].link_type == 'external_link'


def test_determine_type_category_link(link_extractor, content_id):
    html = f'''<div id="{content_id}"><a href="/wiki/Category:Programming_languages">Category</a></div>'''
    links = link_extractor.extract(
        'https://en.wikipedia.org/wiki/Main_Page', html, 1)
    assert links[0].link_type == 'category_link'


def test_determine_type_nofollow_external_link(link_extractor, content_id):
    html = f'''<div id="{content_id}"><a href="http://example.com" rel="nofollow">NoFollow</a></div>'''
    links = link_extractor.extract(
        'https://en.wikipedia.org/wiki/Main_Page', html, 1)
    assert links[0].link_type == 'external_link_nofollow'


def test_determine_type_missing_href(link_extractor, content_id):
    html = f'''<div id="{content_id}"><a>No href</a></div>'''
    links = link_extractor.extract(
        'https://en.wikipedia.org/wiki/Main_Page', html, 1)
    assert len(links) == 0
