from urllib.parse import urlparse, urljoin, urlunparse
from config import EXCLUDED_PREFIXES, WIKI_BASE

# TODO: pull any common utility function into the
# my python-utilities package


def normalize_url(href: str) -> str:
    # Convert relative URL to absolute
    full_url = urljoin(WIKI_BASE, href)

    # Remove fragments (#section) and query params (?foo=bar)
    parsed = urlparse(full_url)
    cleaned = parsed._replace(fragment="", query="")
    return urlunparse(cleaned)


def is_external_link(href):
    parsed = urlparse(href)
    return parsed.scheme in ["http", "https"] and "wikipedia.org" not in parsed.netloc


def has_excluded_prefix(href):
    # strip fragment/query to test path alone
    path = urlparse(href).path

    # check if it's in any excluded namespace
    for prefix in EXCLUDED_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def is_home_page(href):
    parsed = urlparse(href)
    return parsed.path.strip("/") == "" and parsed.netloc in ["", "en.wikipedia.org"]
