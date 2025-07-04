#!/bin/bash
set -e

echo "🔧 Using Docker context: distribute-dev"
docker context use distribute-dev

echo "🧹 Shutting down previous containers..."
docker compose down -v

echo "🔨 Building images..."
docker compose build --no-cache

echo "🚀 Starting core infrastructure (RabbitMQ, Postgres, Redis, etc)..."
docker compose up \
  rabbitmq rabbitmq_seeder postgres postgres_initiator redis pgadmin db_service scheduler \
  -d --remove-orphans

echo "⏳ Waiting 5s before starting crawlers..."
sleep 5

# === Batch 1 ===
echo "🚀 Starting Crawler Batch 0..."
docker compose up \
  --scale parser=2 \
  -d --remove-orphans

echo "⏳ Waiting 10s before next batch..."
sleep 10

# === Batch 2 ===
echo "🚀 Starting Crawler Batch 1..."
docker compose up \
  --scale crawler_noproxy=2 \
  --scale crawler_la=2 \
  --scale crawler_san_jose=2 \
  -d --remove-orphans

echo "⏳ Waiting 10s before next batch..."
sleep 10

# === Batch 3 ===
echo "🚀 Starting Crawler Batch 2..."
docker compose up \
  --scale crawler_boca_raton=2 \
  --scale crawler_las_vegas=2 \
  --scale crawler_buffalo=2 \
  -d --remove-orphans

echo "⏳ Waiting 10s before final batch..."
sleep 10

# === Batch 4 ===
echo "🚀 Starting Crawler Batch 4..."
docker compose up \
  --scale crawler_nyc=2 \
  --scale crawler_dallas=2 \
  --scale crawler_victoria=2 \
  -d --remove-orphans

echo "⏳ Waiting 10s before final batch..."
sleep 10

# === Batch 5 ===
echo "🚀 Starting Crawler Batch 5..."
docker compose up \
  --scale crawler_ashburn=2 \
  --scale crawler_reston=2 \
  -d --remove-orphans

echo "✅ All services started successfully!"
echo "📋 Use 'docker ps' or 'docker logs -f scheduler' to monitor"
