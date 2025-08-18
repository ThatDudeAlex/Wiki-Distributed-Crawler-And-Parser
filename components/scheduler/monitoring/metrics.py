from prometheus_client import Counter, Histogram

# Counters
SCHEDULER_MESSAGES_RECEIVED_TOTAL = Counter(
    "scheduler_messages_received_total",
    "Total messages received by the scheduler message handler",
    ["status"]
)

SCHEDULER_MESSAGE_FAILURES_TOTAL = Counter(
    "scheduler_message_failures_total",
    "Unexpected exceptions in the scheduler message handler",
    ["error_type"]
)

SCHEDULER_PUBLISHED_MESSAGES_TOTAL = Counter(
    "scheduler_published_messages_total",
    "Total messages published to RabbitMQ queues by the scheduler",
    ["status"]
)

# Total links received from the parser
SCHEDULER_LINKS_RECEIVED_TOTAL = Counter(
    "scheduler_links_received_total",
    "Total number of links received for scheduling"
)

# Links deduplicated via Redis (already seen before)
SCHEDULER_LINKS_DEDUPLICATED_TOTAL = Counter(
    "scheduler_links_deduplicated_total",
    "Number of links skipped due to being seen in Redis"
)

# Links filtered by domain, depth, robots.txt, etc.
FILTERED_LINKS_TOTAL = Counter(
    "scheduler_links_filtered_total",
    "Links filtered out before scheduling",
    ["filter_type"]
)


# Links that passed all checks and were published for crawling
SCHEDULER_LINKS_SCHEDULED_TOTAL = Counter(
    "scheduler_links_scheduled_total",
    "Number of links published to the scheduling queue"
)

# Time taken to process a batch of links
SCHEDULER_PROCESSING_DURATION_SECONDS = Histogram(
    "scheduler_processing_duration_seconds",
    "Time taken to process a batch of discovered links",
    ['stage']
)

# Optional: Track Redis-related issues if needed
SCHEDULER_REDIS_ERRORS_TOTAL = Counter(
    "scheduler_redis_errors_total",
    "Number of Redis operation failures in scheduler",
    ["operation"]
)
