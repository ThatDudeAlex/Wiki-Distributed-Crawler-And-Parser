from prometheus_client import Counter, Histogram

# Counters
PARSER_MESSAGES_RECEIVED_TOTAL = Counter(
    "parser_messages_received_total",
    "Total messages received by parser message handler",
    ["status"]
)

# TODO: reneame metric to parser_failures_total
PARSER_MESSAGE_FAILURES_TOTAL = Counter(
    "parser_message_failures_total",
    "Unexpected exceptions in parser message handler",
    ["error_type"]
)

PAGES_PARSED_TOTAL = Counter(
    "pages_parsed_total",
    "Total number of parsing tasks received"
)

LINKS_EXTRACTED_TOTAL = Counter(
    "parser_links_extracted_total",
    "Total number of links extracted"
)

PUBLISHED_MESSAGES_TOTAL = Counter(
    "parser_published_messages_total",
    "Total messages published to RabbitMQ queues by the parser",
    ["queue", "status"]  # e.g. queue="parsed_content_to_save", status="success"
)

# Histograms for latency
STAGE_DURATION_SECONDS = Histogram(
    "parser_stage_duration_seconds",
    "Time spent in each parsing stage",
    ["stage"]
)