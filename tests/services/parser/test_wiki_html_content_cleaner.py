import pytest
from bs4 import BeautifulSoup, Tag
from unittest.mock import Mock, patch
from components.parser.core.wiki_html_content_cleaner import clean_wiki_html_content


@pytest.fixture
def logger():
    return Mock()


@pytest.fixture
def main_div():
    return """
    <div id="mw-content-text">
        <p>This is <b>important</b> content.</p>
        <div class="navbox">Remove this navbox</div>
        <script>alert("bad")</script>
        <style>.hidden {}</style>
        <!-- Comment -->
    </div>
    """


def test_valid_cleaning(logger, main_div):
    soup = BeautifulSoup(main_div, "lxml")
    tag = soup.find("div", id="mw-content-text")

    with patch("components.parser.core.wiki_html_content_cleaner.WIKIPEDIA_BOILERPLATE_SELECTORS", [".navbox"]):
        cleaned = clean_wiki_html_content(tag, logger)

    assert "important content" in cleaned
    assert "Remove this navbox" not in cleaned
    assert "alert" not in cleaned
    assert "Comment" not in cleaned
    assert "hidden" not in cleaned
    logger.info.assert_called_once()


def test_none_input_returns_empty_string(logger):
    result = clean_wiki_html_content(None, logger)
    assert result == ""
    logger.warning.assert_called_once_with(
        "clean_wiki_html_content received None")


def test_only_scripts_and_styles(logger):
    html = "<div><script>bad()</script><style>.cls {}</style><!-- comment --></div>"
    soup = BeautifulSoup(html, "lxml")
    div = soup.div

    cleaned = clean_wiki_html_content(div, logger)
    assert cleaned == ""


def test_no_removable_elements(logger):
    html = "<div><p>Clean text remains</p></div>"
    soup = BeautifulSoup(html, "lxml")
    cleaned = clean_wiki_html_content(soup.div, logger)
    assert cleaned == "Clean text remains"


def test_invalid_html_still_works(logger):
    html = "<div><p>Unclosed paragraph"
    soup = BeautifulSoup(html, "lxml")
    cleaned = clean_wiki_html_content(soup.div, logger)
    assert "Unclosed paragraph" in cleaned


def test_selector_not_present(logger):
    html = "<div><p>Hello world</p></div>"
    soup = BeautifulSoup(html, "lxml")
    with patch("components.parser.core.wiki_html_content_cleaner.WIKIPEDIA_BOILERPLATE_SELECTORS", [".not-present"]):
        cleaned = clean_wiki_html_content(soup.div, logger)
    assert "Hello world" in cleaned


def test_logs_and_returns_empty_on_exception(logger):
    # Force BeautifulSoup to raise an exception
    with patch("components.parser.core.wiki_html_content_cleaner.BeautifulSoup", side_effect=Exception("parse error")):
        html = "<div>text</div>"
        soup = BeautifulSoup(html, "lxml")
        result = clean_wiki_html_content(soup.div, logger)

    assert result == ""
    logger.error.assert_called_once()
