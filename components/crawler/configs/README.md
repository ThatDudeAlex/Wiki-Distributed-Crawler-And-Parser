# Crawler Configurations

This folder contains environment-specific YAML configuration files for the `crawler` component.

---

## Files

- `crawler_dev.yml`  
  Development configuration with:
  - Verbose logging (`DEBUG`)
  - Lower retry thresholds
  - Short recrawl interval for testing

- `crawler_prod.yml`  
  Production-oriented configuration with:
  - Log level set to `INFO`
  - Higher retry attempts
  - Longer recrawl interval (e.g., 8 days)

---

## Configuration Sections

| Key                        | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| `logging`                  | Controls log level and file logging                                         |
| `rate_limit`               | Max requests per period (enforced via `ratelimit`)                          |
| `requests`                 | HTTP request behavior (headers, timeouts, retries)                          |
| `download_retry`           | How many times to retry HTML file download and grace period between retries |
| `recrawl_interval`         | Seconds before a page can be crawled again                                  |
| `storage_path`             | Directory where compressed HTML files are saved                             |

---

## How it's used

The correct config file is loaded based on your environment setting (e.g., `APP_ENV=dev`). The path is resolved dynamically via:

```
components/crawler/main.py -> shared/config_loader.py
```
