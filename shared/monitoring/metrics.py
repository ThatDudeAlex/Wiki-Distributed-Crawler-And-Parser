from prometheus_client import Counter, Histogram

# Counters
CRAWL_PAGES_TOTAL = Counter(
    'crawl_pages_total',
    'Total number of pages crawled by the CrawlerService',
    ['status']  # Label to distinguish success/failure
)

CRAWL_PAGES_FAILURES_TOTAL = Counter(
    'crawl_pages_failures_total',
    'Total number of failed page crawls',
    ['error_type', 'crawl_status']  # Labels for detailed error reporting
)

# Histograms for latency
PAGE_CRAWL_LATENCY_SECONDS = Histogram(
    'page_crawl_latency_seconds',
    'Latency of page crawl in seconds.',
    ['status']  # Label to distinguish success/failure
)
