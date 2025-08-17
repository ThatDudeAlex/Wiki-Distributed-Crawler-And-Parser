from prometheus_client import Counter, Histogram

DISPATCHER_LINKS_FETCHED_TOTAL = Counter(
    "dispatcher_links_fetched_total",
    "Number of links fetched from the DB for crawling"
)

DISPATCHER_CRAWL_TASKS_PUBLISHED_TOTAL = Counter(
    "dispatcher_crawl_tasks_published_total",
    "Number of crawl tasks published to the crawl queue",
    ["status"]
)

DISPATCHER_DISPATCH_ERRORS_TOTAL = Counter(
    "dispatcher_dispatch_errors_total",
    "Number of dispatch loop errors"
)

DISPATCHER_EMPTY_DB_STARTUP_TOTAL = Counter(
    "dispatcher_empty_db_startup_total",
    "Number of times the dispatcher detected an empty DB at startup"
)

DISPATCHER_DISPATCH_LATENCY_SECONDS = Histogram(
    "dispatcher_dispatch_latency_seconds",
    "Latency for one dispatch cycle"
)
