# Web Crawler

> HTTP-based worker that crawls Wikipedia pages, downloads HTML, and pushes content to the parsing and storage pipelines.

---

## Purpose

This service is responsible for:

- Consuming crawl jobs from the RabbitMQ queue: `urls_to_crawl`

- Making HTTP GET requests to target URLs

- Compressing and saving the raw HTML content

- Recording metadata such as:
  - Final URL (after redirects)
  - Path to the saved compressed HTML file

- Publishing results to downstream queues for parsing and database insertion

---

## RabbitMQ Queues

| Direction   | Queue Name         | Purpose                              |
|-------------|--------------------|--------------------------------------|
| Consumes    | `urls_to_crawl`     | URLs to fetch via HTTP               |
| Publishes   | `pages_to_parse`    | Sends compressed HTML for parsing    |
| Publishes   | `save_page_metadata`| Sends page metadata for DB insertion |

---

## Notes

- Uses rate-limited requests

- Compressed files are stored in: `/data/html/` (or as configured in YAML)

- Works in parallel via multiple container replicas

- Configuration is loaded via `shared/config_loader.py` from YAML and `.env`

---

