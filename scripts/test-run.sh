#!/bin/bash
set -e

echo "🚀 Step 0: Teardown Current Containers"
docker compose -f docker/docker-compose.yml down -v
echo "⏳ Waiting 2s for core infra init"
sleep 5

echo "🚀 Step 1: Building & Deploying Core Infrastructure..."
docker compose -f docker/docker-compose.yml build --no-cache rabbitmq postgres postgres_initiator redis
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml up -d rabbitmq postgres postgres_initiator redis --remove-orphans
echo "⏳ Waiting 2s for core infra to settle..."
sleep 2


echo "🚀 Step 2: Building & Deploying DB Services (db_reader + db_writer)..."
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml build --no-cache db_reader db_writer
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml up -d db_reader db_writer --remove-orphans
echo "⏳ Waiting 2s for db_reader/db_writer to boot..."
sleep 2


echo "🚀 Step 3: Building & Deploying Scheduler"
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml build --no-cache scheduler
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml up -d scheduler --remove-orphans
echo "⏳ Waiting 2s before scaling parser..."
sleep 2


echo "🚀 Step 4: Building & Deploying Parser"
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml build --no-cache parser
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml up -d parser --remove-orphans
echo "⏳ Waiting 2s before Crawler..."
sleep 2


echo "🚀 Step 4: Building & Deploying crawler_noproxy"
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml build --no-cache crawler_noproxy
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml up -d crawler_noproxy --remove-orphans
echo "⏳ Waiting 2s before Seeding Queue..."
sleep 2


echo "🚀 Step 5: Turning Up Dispatcher..."
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml build --no-cache dispatcher
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml up -d dispatcher --remove-orphans


echo "🎉 All components deployed successfully!"
sleep 2

docker compose -f docker/docker-compose.yml logs -f