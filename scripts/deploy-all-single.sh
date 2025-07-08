#!/bin/bash
set -e


# ========== Infrastructure Services Init & Deployment ==========


echo "🚀 Step 1: Building & Deploying Core Infrastructure..."
docker compose build --no-cache rabbitmq postgres pgadmin postgres_initiator redis
docker compose up -d rabbitmq postgres pgadmin postgres_initiator redis --remove-orphans
echo "⏳ Waiting 7s for core infra to settle..."
sleep 7


# ========== DB Writer/Reader Init & Deployment ==========

echo "🚀 Step 2: Building & Deploying DB Services (db_reader + db_writer)..."
docker compose build --no-cache db_reader db_writer
docker compose up -d --scale db_writer=$DB_WRITER_COUNT --scale db_reader=$DB_READER_COUNT db_reader db_writer --remove-orphans
echo "⏳ Waiting 7s for db_reader/db_writer to boot..."
sleep 7


# ========== Schedulers Init & Deployment ==========


echo "🚀 Step 3: Building & Gradually Scaling Scheduler (2 → 8)..."
docker compose build --no-cache scheduler

current_scheduler_count=2

while [ $current_scheduler_count -le $SCHEDULER_MAX_COUNT ]; do
    echo "🚀 Scaling Scheduler to $current_scheduler_count..."
    docker compose up --scale scheduler=$current_scheduler_count -d scheduler --remove-orphans
    echo "⏳ Sleeping 15s..."
    sleep 15
    current_scheduler_count=$((current_scheduler_count + 2))
done

echo "⏳ Waiting 10s before scaling parsers..."
sleep 10


# ========== Parsers Init & Deployment ==========


echo "🚀 Step 4: Building & Gradually Scaling Parsers (2 → 14)..."
docker compose build --no-cache parser

current_parser_scale=2

while [ $current_parser_scale -le $PARSER_MAX_COUNT ]; do
    echo "🚀 Scaling parser to $current_parser_scale..."
    docker compose up --scale parser=$current_parser_scale -d parser --remove-orphans
    echo "⏳ Sleeping 15s..."
    sleep 15
    current_parser_scale=$((current_parser_scale + 2))
done

echo "✅ Parsers deployed at scale $PARSER_MAX_COUNT."

echo "⏳ Waiting 10s before scaling schedulers..."
sleep 10


# ========== Crawlers Init & Deployment ==========

echo "🚀 Step 5: Building & Deploying Crawlers (11 regions × $CRAWLER_PROXY_COUNT)..."
docker compose build --no-cache \
  crawler_noproxy crawler_la crawler_san_jose crawler_boca_raton \
  crawler_las_vegas crawler_buffalo crawler_nyc crawler_dallas

declare -a CRAWLERS=(
  crawler_noproxy
  crawler_la
  crawler_san_jose
  crawler_boca_raton
  crawler_las_vegas
  crawler_buffalo
  crawler_nyc
  crawler_dallas
  crawler_ashburn
  crawler_reston
  crawler_victoria
)

for crawler in "${CRAWLERS[@]}"; do
  echo "🚀 Deploying $crawler with scale=$CRAWLER_PROXY_COUNT..."
  docker compose up --scale $crawler=$CRAWLER_PROXY_COUNT -d $crawler --remove-orphans
  echo "⏳ Sleeping 15s before next crawler..."
  sleep 15
done


# ========== Queue Seeder ==========


echo "🚀 Step 6: Seeding Queue..."
docker compose build --no-cache rabbitmq_seeder
docker compose up -d rabbitmq_seeder --remove-orphans
echo "⏳ Waiting 7s for seeder to settle..."
sleep 7


# ========== Dispatcher Init & Deployment ==========


echo "🚀 Step 7: Turning Up Dispatcher..."
docker compose build --no-cache dispatcher
docker compose up -d dispatcher --remove-orphans
sleep 2

echo "🎉 All components deployed successfully!"
