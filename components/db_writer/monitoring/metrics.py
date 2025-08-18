from prometheus_client import Counter, Histogram

# Counters
DB_WRITER_MESSAGES_RECEIVED_TOTAL = Counter(
    "db_writer_messages_received_total",
    "Total messages received by db_writer message handler",
    ["status"]
)

DB_WRITER_MESSAGE_FAILURES_TOTAL = Counter(
    "db_writer_message_failures_total",
    "Unexpected exceptions in db_writer message handler",
    ["error_type"]
)

# Successful operations per function
DB_WRITER_INSERT_SUCCESS_TOTAL = Counter(
    "db_writer_insert_success_total",
    "Count of successful DB inserts or upserts",
    ["operation"]
)

# Failed operations per function
DB_WRITER_INSERT_FAILURE_TOTAL = Counter(
    "db_writer_insert_failure_total",
    "Count of failed DB inserts or upserts",
    ["operation"]
)

# Latency per operation
DB_WRITER_INSERT_LATENCY_SECONDS = Histogram(
    "db_writer_insert_latency_seconds",
    "Latency for DB insert operations in seconds",
    ["operation"]
)
