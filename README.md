# Wiki Distributed Crawler & Parser

![CI/CD](https://github.com/ThatDudeAlex/Wiki-Distributed-Crawler-And-Parser/actions/workflows/ci.yml/badge.svg)

## Overview
A **search-engine style distributed web crawling system** built to crawl and parse **Wikipedia article pages**.  
The system is composed of **7 independent worker services** connected via RabbitMQ, each of which can be scaled horizontally.  

It demonstrates a **distributed, event-driven architecture** capable of crawling at high throughput (6.4M+ pages/day on a 24-core VM).

---

## Architecture

### Core Components
1. **Crawler** – fetches HTML, compresses & stores it, publishes metadata for storage and parsing. (Rate limited: 1 req/s per crawler)  
2. **Parser** – extracts title, content, categories, and links; publishes parsed content and extracted links.  
3. **Scheduler** – filters to article pages, normalizes/dedupes via Redis, checks robots.txt, stores valid links.  
4. **DB Reader (HTTP API)** – serves read-only queries to PostgreSQL (bypasses RabbitMQ).  
5. **DB Writer** – consumes messages and writes data into PostgreSQL.  
6. **Dispatcher** – requests scheduled URLs from DB Reader and pushes them into the `urls_to_crawl` queue.  
7. **Rescheduler** – periodically re-queues pages due for recrawl (~8 days).  

### System Diagram
![System Architecture](https://res.cloudinary.com/dmllp7gur/image/upload/v1755573701/Screenshot_2025-08-18_at_11.20.21_PM_b9igie.png)

### RabbitMQ Queues
![RabbitMQ Queues](https://res.cloudinary.com/dmllp7gur/image/upload/v1755366075/Screenshot_2025-08-16_at_1.40.03_PM_qpbjjh.png)

### Tech Stack
- **Python**
- **Docker Compose** (dev & prod)  
- **RabbitMQ** for messaging & load balancing  
- **PostgreSQL + SQLAlchemy** for persistence  
- **Redis** for caching & deduplication  
- **Prometheus + Grafana + cAdvisor + node-exporter + pgAdmin** for monitoring  
- **Webshare proxies** for geo-distributed crawling  

---

## Repo Structure (highlights)

```
components/       # Each independent service
docker/           # Docker Compose, scaling configs, monitoring stack
scripts/          # Deployment + helper scripts
shared/           # Shared utilities (config loader, logging, etc.)
tests/            # Unit + integration tests
```

Example `docker/` layout:  
```
docker/
├── docker-compose.yml
├── environments/
│   ├── docker-compose.dev.yml
│   ├── docker-compose.prod.yml
│   └── deploy_configs/
│       ├── scaling.dev.yml
│       └── scaling.prod.yml
└── monitoring/
    ├── docker-compose.monitoring.yml
    └── configs/ (Grafana dashboards, Prometheus, pgAdmin)
```

---

## Configuration

Each component has `configs/` with `*_dev.yml` and `*_prod.yml`.  
Examples:  

- **Crawler**  
  - Rate limit (`1 req/sec`)  
  - Retry + timeout policy  
  - Storage path for HTML  
  - Recrawl interval (`8 days`)  

- **Dispatcher**  
  - `dispatch_count`: how many URLs per tick  
  - `dispatch_tick`: seconds between batches  
  - `seed_urls`: starting points  

- **Scheduler**  
  - Filters (article-only)  
  - `max_depth` crawl depth  

- **Rescheduler**  
  - `rescheduling_tick`: how often to rescan for expired pages  

**.env (docker/)** – sets RabbitMQ, Postgres, Redis, service endpoints, proxies.  
**Scaling YAMLs** – `scaling.dev.yml` / `scaling.prod.yml` define how many instances per service.  

---

## Configure Environment Variables

Before running the system, copy the example environment file:

```bash
cp docker/.env.example docker/.env
```

By default, this uses placeholder credentials (`postgres/postgres`, `guest/guest`).  
For production or custom setups, edit `docker/.env` and update values:

- `RABBITMQ_USER` / `RABBITMQ_PASS`  
- `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB`  
- `DATABASE_URL`  
- `DB_READER_HOST`  

This step is required before running the deployment script.

## Running the System

### Prerequisites
- Docker & Docker Compose installed  
- (Optional) Proxies for crawlers  

### Quickstart
```bash
# Clone repository
git clone https://github.com/ThatDudeAlex/Wiki-Distributed-Crawler-And-Parser.git
cd Wiki-Distributed-Crawler-And-Parser/

# Deploy in dev mode without monitoring
./scripts/deploy-system-arm64 --env dev

# Deploy in dev mode with monitoring
./scripts/deploy-system-arm64 --env dev --monitoring
```

This script handles environment selection, scaling configs, and launching containers.  
Linux/Windows binaries are planned; current binary is for ARM64 (Mac).  

### Resetting State
```bash
scripts/reset-vm-docker-state.sh
```

---

## Performance

- Test setup: Proxmox Ubuntu VM, **24 cores, 32 GiB RAM**  
- Deployment: 117 containers  
  - 75 crawlers, 12 parsers, 14 schedulers, 4 db_writers, 1 db_reader, 1 dispatcher, 1 rescheduler + monitoring stack  
- Throughput: **75 pages/sec** (~6.48M/day)  

---

## Continuous Integration

This project uses **GitHub Actions** for CI/CD to enforce code quality and reliability.

- **Linting**: Uses [Ruff](https://github.com/astral-sh/ruff) to enforce Python style and catch errors.  
- **Configuration checks**: Validates that crawler proxy settings are correctly disabled in dev/prod environments.  
- **Unit tests**: Runs automated tests against PostgreSQL in a service container.  
- **Branch enforcement**: Ensures only `crawler_noproxy` is deployed on `main`.  

Workflow file: [ci.yml](.github/workflows/ci.yml)

---

## Limitations & Roadmap

- [x] Distributed crawling & parsing  
- [x] Monitoring stack (Docker Compose)  
- [x] Continuous Integration (linting, config checks, unit tests)  
- [ ] Kubernetes support  
- [ ] Continuous Deployment (auto-deploy images / cluster rollout)  
- [ ] Dynamic proxy rotation (geo-aware balancing)  

---

## Why This Project Matters

This system simulates how **early search engines** built large-scale web crawlers:  
- Independent worker services  
- Event-driven, message-queue based communication  
- Horizontal scaling of components  
- Caching, deduplication, rescheduling, and monitoring  

It’s a practical demonstration of distributed systems design, scalability, and observability — valuable in real-world search/crawl pipelines.

---

## License
MIT License – see [LICENSE](LICENSE) file for details.
