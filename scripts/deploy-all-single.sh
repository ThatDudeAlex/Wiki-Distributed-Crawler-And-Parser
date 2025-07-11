#!/bin/bash
set -e
set -a
source .env
set +a


# ========== Infrastructure Services Init & Deployment ==========


echo "🚀 Step 1: Building & Deploying Core Infrastructure..."
docker compose build --no-cache rabbitmq postgres pgadmin postgres_initiator redis
docker compose up -d rabbitmq postgres pgadmin postgres_initiator redis --remove-orphans
echo "⏳ Waiting 7s for core infra to settle..."
sleep 2


# ========== DB Writer/Reader Init & Deployment ==========

echo "🚀 Step 2: Building & Deploying DB Services (db_reader + db_writer)..."
docker compose build --no-cache db_reader db_writer
docker compose up -d --scale db_writer=$DB_WRITER_COUNT --scale db_reader=$DB_READER_COUNT db_reader db_writer --remove-orphans
echo "⏳ Waiting 7s for db_reader/db_writer to boot..."
sleep 2


# ========== Schedulers Init & Deployment ==========


echo "🚀 Step 3: Building & Gradually Scaling Scheduler (2 → 8)..."
docker compose build --no-cache scheduler

current_scheduler_count=2

while [ $current_scheduler_count -le $SCHEDULER_MAX_COUNT ]; do
    echo "🚀 Scaling Scheduler to $current_scheduler_count..."
    docker compose up --scale scheduler=$current_scheduler_count -d scheduler --remove-orphans
    echo "⏳ Sleeping 5s..."
    sleep 2
    current_scheduler_count=$((current_scheduler_count + 2))
done

echo "⏳ Waiting 5s before scaling parsers..."
sleep 2


# ========== Parsers Init & Deployment ==========


echo "🚀 Step 4: Building & Gradually Scaling Parsers (2 → 14)..."
docker compose build --no-cache parser

current_parser_scale=2

while [ $current_parser_scale -le $PARSER_MAX_COUNT ]; do
    echo "🚀 Scaling parser to $current_parser_scale..."
    docker compose up --scale parser=$current_parser_scale -d parser --remove-orphans
    echo "⏳ Sleeping 5s..."
    sleep 2
    current_parser_scale=$((current_parser_scale + 2))
done

echo "✅ Parsers deployed at scale $PARSER_MAX_COUNT."

echo "⏳ Waiting 5s before scaling schedulers..."
sleep 2


# ========== Crawlers Init & Deployment ==========

echo "🚀 Step 5: Building & Deploying Crawlers (53 regions × $CRAWLER_PROXY_COUNT)..."
docker compose build --no-cache \
  crawler_noproxy \
  crawler_santa_cruz1 crawler_santa_cruz2 crawler_santa_clara crawler_san_jose \
  crawler_la1 crawler_la2 crawler_la3 crawler_la4 crawler_la5 crawler_la6 \
  crawler_la7 crawler_la8 crawler_la9 crawler_la10 \
  crawler_boca_raton \
  crawler_kansas_city \
  crawler_abbeville \
  crawler_las_vegas1 crawler_las_vegas2 \
  crawler_piscataway1 crawler_piscataway2 crawler_piscataway3 \
  crawler_buffalo1 crawler_buffalo2 crawler_buffalo3 crawler_buffalo4 crawler_buffalo5 \
  crawler_nyc1 crawler_nyc2 crawler_nyc3 crawler_nyc4 crawler_nyc5 crawler_nyc6 crawler_nyc7 \
  crawler_dallas1 crawler_dallas2 \
  crawler_victoria1 crawler_victoria2 crawler_victoria3 \
  crawler_orem1 crawler_orem2 \
  crawler_ashburn1 crawler_ashburn2 crawler_ashburn3 crawler_ashburn4 \
  crawler_reston1 crawler_reston2 crawler_reston3 \
  crawler_dc1 crawler_dc2 crawler_dc3 crawler_dc4

# Declare all crawler names
declare -a CRAWLERS=(
  crawler_noproxy

  # California
  crawler_santa_cruz1
  crawler_santa_cruz2
  crawler_santa_clara
  crawler_san_jose
  crawler_la1
  crawler_la2
#   crawler_la3
#   crawler_la4
#   crawler_la5
#   crawler_la6
#   crawler_la7
#   crawler_la8
#   crawler_la9
#   crawler_la10

  # Florida
  crawler_boca_raton

  # Missouri
  crawler_kansas_city

  # Louisiana
  crawler_abbeville

  # Nevada
  crawler_las_vegas1
#   crawler_las_vegas2

  # New Jersey
  crawler_piscataway1
#   crawler_piscataway2
#   crawler_piscataway3

#   # New York
  crawler_buffalo1
  crawler_buffalo2
#   crawler_buffalo3
#   crawler_buffalo4
#   crawler_buffalo5
  crawler_nyc1
  crawler_nyc2
#   crawler_nyc3
#   crawler_nyc4
#   crawler_nyc5
#   crawler_nyc6
#   crawler_nyc7

#   # Texas
  crawler_dallas1
#   crawler_dallas2
  crawler_victoria1
#   crawler_victoria2
#   crawler_victoria3

#   # Utah
#   crawler_orem1
#   crawler_orem2

  # Virginia
  crawler_ashburn1
#   crawler_ashburn2
#   crawler_ashburn3
#   crawler_ashburn4
#   crawler_reston1
#   crawler_reston2
#   crawler_reston3

#   # Washington DC
  crawler_dc1
#   crawler_dc2
#   crawler_dc3
#   crawler_dc4
)

# Deploy all crawlers
for crawler in "${CRAWLERS[@]}"; do
  echo "🚀 Deploying $crawler with scale=$CRAWLER_PROXY_COUNT..."
  docker compose up --scale $crawler=$CRAWLER_PROXY_COUNT -d $crawler --remove-orphans
  echo "⏳ Sleeping 2s before next crawler..."
  sleep 2
done

# ========== Dispatcher Init & Deployment ==========


echo "🚀 Step 6: Turning Up Dispatcher..."
docker compose build --no-cache dispatcher
docker compose up -d dispatcher --remove-orphans
sleep 2

echo "🎉 All components deployed successfully!"
