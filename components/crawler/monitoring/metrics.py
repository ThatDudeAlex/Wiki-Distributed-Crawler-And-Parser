from prometheus_client import Counter, Histogram

# Counters
CRAWLER_MESSAGES_RECEIVED_TOTAL = Counter(
    "crawler_messages_received_total",
    "Total messages received by crawler message handler",
    ["status"]
)

CRAWLER_MESSAGE_FAILURES_TOTAL = Counter(
    "crawler_message_failures_total",
    "Unexpected exceptions in crawler message handler",
    ["error_type"]
)

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

CRAWLER_HTML_DOWNLOAD_RETRIES_TOTAL = Counter(
    "crawler_html_download_retries_total",
    "Total number of HTML download retries attempted (excluding initial attempt)",
    ["url_host"]
)

PUBLISHED_MESSAGES_TOTAL = Counter(
    "crawler_published_messages_total",
    "Total messages published to RabbitMQ queues by the crawler",
    ["queue", "status"]  # e.g. queue="parsed_content_to_save", status="success"
)

# Histograms for latency
PAGE_CRAWL_LATENCY_SECONDS = Histogram(
    'page_crawl_latency_seconds',
    'Time spent in each crawler stage',
    ['stage']
)


