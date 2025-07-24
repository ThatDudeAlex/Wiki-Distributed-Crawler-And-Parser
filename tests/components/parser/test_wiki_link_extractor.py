import re
from unittest.mock import Mock

import pytest
from components.parser.core.wiki_link_extractor import PageLinkExtractor
from shared.configs.config_loader import component_config_loader


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
