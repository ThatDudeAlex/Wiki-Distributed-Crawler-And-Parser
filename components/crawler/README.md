# Web Crawler

> HTTP-based worker that fetches Wikipedia pages, stores compressed HTML, and dispatches metadata and content to downstream services.


## Overview

This service is part of a horizontally scalable crawling system.  
Each instance is rate-limited (e.g., 1 request/sec), but multiple replicas can be run in parallel to achieve higher aggregate throughput.


## Responsibilities

- Consumes crawl jobs from the RabbitMQ queue: `urls_to_crawl`
- Performs rate-limited HTTP GET requests to fetch pages
- Saves compressed HTML content to disk
- Records crawl metadata, including:
  - Final resolved URL (after redirects)
  - Path to the compressed HTML file
  - HTTP status code, headers, and timestamps
- Publishes messages to:
  - Trigger downstream parsing
  - Store crawl results in the database


## Queues

| Direction | Queue Name           | Description                          |
|-----------|----------------------|--------------------------------------|
| Consumes  | `urls_to_crawl`      | Incoming crawl jobs                  |
| Publishes | `pages_to_parse`     | Triggers parsers to process HTML     |
| Publishes | `save_page_metadata` | Sends crawl metadata for persistence |


## Configuration

- Configuration is loaded via `shared/config_loader.py`
- YAML files (e.g., `crawler_dev.yml`, `crawler_prod.yml`) define:
  - Rate limits
  - HTTP headers and timeouts
  - Retry behavior
  - Storage path
- Environment variables can override YAML values


## Storage

- Compressed HTML is stored in `/data/html/`  
  *(or as defined by `storage_path` in config)*


## Scaling and Proxy Support

This service supports horizontal scaling by running multiple container replicas.

Each replica can be configured with a different HTTP/S proxy to enable:
- Geographically distributed crawling
- Load balancing across IPs
- Evasion of IP-based rate limits or bans

### Example `docker-compose.yml`:

```yaml
crawler_santa_cruz1:
  <<: *crawler-common
  environment:
    - HTTP_PROXY=${CA_SANTA_CRUZ1_PROXY}
    - HTTPS_PROXY=${CA_SANTA_CRUZ1_PROXY}
```

Set proxy environment variables (`HTTP_PROXY`, `HTTPS_PROXY`) per instance via `.env` to route requests through different cities or countries.
