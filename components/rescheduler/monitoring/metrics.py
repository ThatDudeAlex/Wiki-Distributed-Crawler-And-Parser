from prometheus_client import Counter, Histogram

RESCHEDULER_PAGES_RESCHEDULED_TOTAL = Counter(
    "rescheduler_pages_rescheduled_total",
    "Total number of pages that were rescheduled"
)

RESCHEDULER_CRAWL_TASKS_PUBLISHED_TOTAL = Counter(
    "rescheduler_crawl_tasks_published_total",
    "Total number of crawl tasks published by the rescheduler"
)

RESCHEDULER_ERRORS_TOTAL = Counter(
    "rescheduler_errors_total",
    "Total number of errors encountered during rescheduling"
)

RESCHEDULER_RESCHEDULE_LATENCY_SECONDS = Histogram(
    "rescheduler_reschedule_latency_seconds",
    "Time taken for a rescheduling iteration"
)
