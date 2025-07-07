#!/bin/bash
set -e

echo "🚀 Step 1: Building & Deploying Core Infrastructure..."
docker compose build --no-cache rabbitmq postgres postgres_initiator redis
docker compose up -d rabbitmq postgres postgres_initiator redis --remove-orphans
echo "⏳ Waiting 2s for core infra to settle..."
sleep 2

echo "🚀 Step 2: Building & Deploying DB Services (db_reader + db_writer)..."
docker compose build --no-cache db_reader db_writer
docker compose up -d db_reader db_writer --remove-orphans
echo "⏳ Waiting 2s for db_reader/db_writer to boot..."
sleep 2

# echo "🚀 Step 3: Building & Deploying Scheduler"
# docker compose build --no-cache scheduler
# docker compose up -d scheduler --remove-orphans

# echo "⏳ Waiting 2s before scaling parser..."
# sleep 2

# echo "🚀 Step 4: Building & Deploying Parser"
# docker compose build --no-cache parser
# docker compose up -d parser --remove-orphans

# echo "⏳ Waiting 2s before Crawler..."
# sleep 2

# echo "🚀 Step 4: Building & Deploying crawler_noproxy"
# docker compose build --no-cache crawler_noproxy
# docker compose up -d crawler_noproxy --remove-orphans

# echo "⏳ Waiting 2s before Seeding Queue..."
# sleep 2

echo "🚀 Step 6: Seeding Queue..."
docker compose build --no-cache rabbitmq_seeder
docker compose up -d rabbitmq_seeder --remove-orphans
echo "⏳ Waiting 2s for Dispatcher"
sleep 2

echo "🚀 Step 6: Booting Dispatcher"
docker compose build --no-cache dispatcher
docker compose up -d dispatcher --remove-orphans


echo "🎉 All components deployed successfully!"
sleep 2

docker compose logs -f
