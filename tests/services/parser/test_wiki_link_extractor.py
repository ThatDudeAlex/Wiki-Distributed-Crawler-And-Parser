import unittest
from unittest.mock import MagicMock
from components.parser.configs.app_configs import WIKIPEDIA_MAIN_BODY_ID
from components.parser.core.wiki_link_extractor import _WikipediaLinkExtractor


class TestWikipediaLinkExtractor(unittest.TestCase):
    def setUp(self):
        self.logger = MagicMock()
        self.extractor = _WikipediaLinkExtractor(logger=self.logger)

    def test_internal_link(self):
        html = f'''<div id="{WIKIPEDIA_MAIN_BODY_ID}"><a href="/wiki/Python_(programming_language)">Python</a></div>'''
        links = self.extractor.extract(
            'https://en.wikipedia.org/wiki/Main_Page', html)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].link_type, 'wikilink')

    def test_external_link(self):
        html = f'''<div id="{WIKIPEDIA_MAIN_BODY_ID}"><a href="http://example.com">Example</a></div>'''
        links = self.extractor.extract(
            'https://en.wikipedia.org/wiki/Main_Page', html)
        self.assertEqual(links[0].link_type, 'external_link')

    def test_category_link(self):
        html = f'''<div id="{WIKIPEDIA_MAIN_BODY_ID}"><a href="/wiki/Category:Programming_languages">Category</a></div>'''
        links = self.extractor.extract(
            'https://en.wikipedia.org/wiki/Main_Page', html)
        self.assertEqual(links[0].link_type, 'category_link')

    def test_nofollow_external_link(self):
        html = f'''<div id="{WIKIPEDIA_MAIN_BODY_ID}"><a href="http://example.com" rel="nofollow">NoFollow</a></div>'''
        links = self.extractor.extract(
            'https://en.wikipedia.org/wiki/Main_Page', html)
        self.assertEqual(links[0].link_type, 'external_link_nofollow')

    def test_missing_href(self):
        html = f'''<div id="{WIKIPEDIA_MAIN_BODY_ID}"><a>No href</a></div>'''
        links = self.extractor.extract(
            'https://en.wikipedia.org/wiki/Main_Page', html)
        self.assertEqual(len(links), 0)
