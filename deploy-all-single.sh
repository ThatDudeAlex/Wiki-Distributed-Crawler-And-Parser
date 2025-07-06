#!/bin/bash
set -e

echo "🚀 Step 1: Building & Deploying Core Infrastructure..."
docker compose build --no-cache rabbitmq postgres pgadmin postgres_initiator redis
docker compose up -d rabbitmq postgres pgadmin postgres_initiator redis --remove-orphans
echo "⏳ Waiting 7s for core infra to settle..."
sleep 7

db_writer_count=1
db_reader_count=1

echo "🚀 Step 2: Building & Deploying DB Services (db_reader + db_writer)..."
docker compose build --no-cache db_reader db_writer
docker compose up -d --scale db_writer=$db_writer_count --scale db_reader=$db_reader_count db_reader db_writer --remove-orphans
echo "⏳ Waiting 7s for db_reader/db_writer to boot..."
sleep 7

echo "🚀 Step 3: Building & Gradually Scaling Scheduler (2 → 8)..."
docker compose build --no-cache scheduler

current_scheduler_count=2
max_scheduler_count=8

while [ $current_scheduler_count -le $max_scheduler_count ]; do
    echo "🚀 Scaling Scheduler to $current_scheduler_count..."
    docker compose up --scale scheduler=$current_scheduler_count -d scheduler --remove-orphans
    echo "⏳ Sleeping 15s..."
    sleep 15
    current_scheduler_count=$((current_scheduler_count + 2))
done

echo "⏳ Waiting 10s before scaling parsers..."
sleep 10

echo "🚀 Step 4: Building & Gradually Scaling Parsers (2 → 14)..."
docker compose build --no-cache parser

current_parser_scale=2
max_parser_scale=14

while [ $current_parser_scale -le $max_parser_scale ]; do
    echo "🚀 Scaling parser to $current_parser_scale..."
    docker compose up --scale parser=$current_parser_scale -d parser --remove-orphans
    echo "⏳ Sleeping 15s..."
    sleep 15
    current_parser_scale=$((current_parser_scale + 2))
done

echo "✅ Parsers deployed at scale $max_parser_scale."

echo "⏳ Waiting 10s before scaling schedulers..."
sleep 10

crawler_proxy_instances=3

echo "🚀 Step 5: Building & Deploying Crawlers (11 regions × $crawler_proxy_instances)..."
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
  echo "🚀 Deploying $crawler with scale=$crawler_proxy_instances..."
  docker compose up --scale $crawler=$crawler_proxy_instances -d $crawler --remove-orphans
  echo "⏳ Sleeping 15s before next crawler..."
  sleep 15
done

echo "🚀 Step 6: Seeding Queue..."
docker compose build --no-cache rabbitmq_seeder
docker compose up -d rabbitmq_seeder --remove-orphans
echo "⏳ Waiting 7s for core infra to settle..."
sleep 7

echo "🎉 All components deployed successfully!"
