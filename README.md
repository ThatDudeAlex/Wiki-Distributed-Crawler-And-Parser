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
```

Run the deployment binary appropriate for your OS:

- **Mac (Apple Silicon / ARM64):**
  ```bash
  ./scripts/deploy-system-arm64 --env dev
  ./scripts/deploy-system-arm64 --env dev --monitoring

  # Example: deploy with production configs
  ./scripts/deploy-system-arm64 --env prod --monitoring
  ```

- **Linux (x86_64):**
  ```bash
  ./scripts/deploy-system-linux --env dev
  ./scripts/deploy-system-linux --env dev --monitoring

  # Example: deploy with production configs
  ./scripts/deploy-system-linux --env prod --monitoring
  ```

- **Windows (x86_64):**
  ```powershell
  .\scripts\deploy-system-windows.exe --env dev
  .\scripts\deploy-system-windows.exe --env dev --monitoring

  # Example: deploy with production configs
  .\scripts\deploy-system-windows.exe --env prod --monitoring
  ```

This deployment script handles environment selection, scaling configs, and launching containers.  
It accepts the following flags:

- `--monitoring` → Determines whether the monitoring stack (Prometheus, Grafana, cAdvisor, node-exporter, pgAdmin) is deployed.  
- `--env` → Specifies which environment configs to use. Available values: `dev` or `prod`.  
  - If `--env` is not provided, the script defaults to **dev** configs.  

You only need Docker & Docker Compose installed.  

### Reset Project Docker State (Safe Reset)
If you only want to clear containers, networks, and volumes **related to this project** (without touching global Docker state), use:

```bash
scripts/reset-project-docker-state.sh
```

This script runs:

```bash
docker compose -f docker/docker-compose.yml down -v
```

It removes all services, networks, and volumes created by the project’s Compose files.  

⚠️ **Note:** Project volumes (e.g., PostgreSQL and Redis data) will also be deleted. If you want to preserve data volumes, run instead:

```bash
docker compose -f docker/docker-compose.yml stop
docker compose -f docker/docker-compose.yml rm -f
```


### Resetting Docker State (Full Cleanup)
This script **stops all containers and prunes all Docker data** on the host connected to the docker context:  
- Stops running containers  
- Removes all containers, images, networks, build cache, and volumes  

⚠️ **Warning:** This is destructive and will wipe *all* Docker state on the machine, not just this project.

```bash
scripts/wipe-docker-host.sh
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
