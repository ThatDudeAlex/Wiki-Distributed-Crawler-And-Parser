from unittest.mock import Mock

import pytest
from components.parser.core.wiki_link_extractor import PageLinkExtractor
from components.parser.configs.parser_config import configs as loaded_configs


@pytest.fixture
def logger():
    return Mock()


@pytest.fixture
def link_extractor(logger):
    return PageLinkExtractor(loaded_configs.selectors, logger)


@pytest.fixture
def content_id():
    return loaded_configs.selectors.content_container_id.lstrip('#')


def test_internal_link(link_extractor, content_id):
    html = f'''<div id="{content_id}"><a href="/wiki/Python_(programming_language)">Python</a></div>'''
    links = link_extractor.extract(
        'https://en.wikipedia.org/wiki/Main_Page', html, 0)
    assert len(links) == 1
    assert links[0].link_type == 'wikilink'


def test_external_link(link_extractor, content_id):
    html = f'''<div id="{content_id}"><a href="http://example.com">Example</a></div>'''
    links = link_extractor.extract(
        'https://en.wikipedia.org/wiki/Main_Page', html, 1
    )
    assert links[0].link_type == 'external_link'


def test_category_link(link_extractor, content_id):
    html = f'''<div id="{content_id}"><a href="/wiki/Category:Programming_languages">Category</a></div>'''
    links = link_extractor.extract(
        'https://en.wikipedia.org/wiki/Main_Page', html, 1)
    assert links[0].link_type == 'category_link'


def test_nofollow_external_link(link_extractor, content_id):
    html = f'''<div id="{content_id}"><a href="http://example.com" rel="nofollow">NoFollow</a></div>'''
    links = link_extractor.extract(
        'https://en.wikipedia.org/wiki/Main_Page', html, 1)
    assert links[0].link_type == 'external_link_nofollow'


def test_missing_href(link_extractor, content_id):
    html = f'''<div id="{content_id}"><a>No href</a></div>'''
    links = link_extractor.extract(
        'https://en.wikipedia.org/wiki/Main_Page', html, 1)
    assert len(links) == 0
