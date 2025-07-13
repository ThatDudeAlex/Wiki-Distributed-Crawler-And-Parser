from prometheus_client import Counter, Histogram

# Counters
PAGES_PARSED_TOTAL = Counter(
    "pages_parsed_total",
    "Total number of parsing tasks received"
)

LINKS_EXTRACTED_TOTAL = Counter(
    "parser_links_extracted_total",
    "Total number of links extracted"
)

# Histograms for latency
STAGE_DURATION_SECONDS = Histogram(
    "parser_stage_duration_seconds",
    "Time spent in each parsing stage",
    ["stage"]
)
