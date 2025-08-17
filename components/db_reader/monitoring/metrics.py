from prometheus_client import Counter, Histogram

# Counters
DB_READER_REQUESTS_RECEIVED_TOTAL = Counter(
    "db_reader_requests_received_total",
    "Total requests received by db_reader",
    ["status"]
)

DB_READER_REQUESTS_FAILURES_TOTAL = Counter(
    "db_reader_requests_failures_total",
    "Unexpected exceptions in db_reader",
    ["error_type"]
)

# Count of links popped from the scheduled_links table
DB_READER_LINKS_POPPED_TOTAL = Counter(
    "db_reader_links_popped_total",
    "Number of links popped from the scheduled_links table"
)

# Count of due pages returned for rescheduling
DB_READER_DUE_PAGES_FOUND_TOTAL = Counter(
    "db_reader_due_pages_found_total",
    "Number of due pages returned for rescheduling"
)

# Count of DB empty checks labeled by outcome
DB_READER_EMPTY_CHECKS_TOTAL = Counter(
    "db_reader_empty_checks_total",
    "Total checks where DB was empty or not",
    ["empty"]
)

# Latency of DB reader operations
DB_READER_QUERY_LATENCY_SECONDS = Histogram(
    "db_reader_query_latency_seconds",
    "Latency for DB reader queries in seconds",
    ["operation"]
)
