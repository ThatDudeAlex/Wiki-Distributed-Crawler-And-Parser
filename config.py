SEED_URL = 'https://en.wikipedia.org/wiki/Computer_science'

MAX_DEPTH = 3

ROBOTS_TXT = 'https://en.wikipedia.org/robots.txt'

WIKI_BASE = "https://en.wikipedia.org"

BASE_HEADERS = {
    'accept': 'text/html',
    'accept-language': 'en-US',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
}

# Wikimedia namespaces
EXCLUDED_PREFIXES = [
    "/wiki/Special:",
    "/wiki/Help:",
    "/wiki/Portal:",
    "/wiki/File:",
    "/wiki/Template:",
    "/wiki/Wikipedia:",
    "/wiki/Talk:",
    "/wiki/Category:",
    "/wiki/Book:",
    "/wiki/User:",
    "/wiki/Module:",
    "/wiki/Project:",
    "/wiki/Main_Page",
]
