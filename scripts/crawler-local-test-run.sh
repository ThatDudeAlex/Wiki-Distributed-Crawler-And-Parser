echo "🚀 Step 1: Teardown Current Infrastructure Containers"
docker compose -f docker/docker-compose.yml stop rabbitmq postgres postgres_initiator redis
docker compose -f docker/docker-compose.yml rm -f rabbitmq postgres postgres_initiator redis
echo "⏳ Waiting 2s for core infra init"
sleep 2

echo "🚀 Step 2: Building & Deploying Core Infrastructure..."
docker compose -f docker/docker-compose.yml build --no-cache rabbitmq postgres postgres_initiator redis
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml up -d rabbitmq postgres postgres_initiator redis --remove-orphans
echo "⏳ Waiting 2s for core infra to settle..."
sleep 2

echo "🚀 Step 3: Building & Deploying DB Services (db_reader + db_writer)..."
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml build --no-cache db_reader db_writer
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml up -d db_reader db_writer --remove-orphans
echo "⏳ Waiting 2s for db_reader/db_writer to boot..."
sleep 2


echo "🚀 Step 4: Building & Deploying Scheduler"
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml build --no-cache scheduler
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml up -d scheduler --remove-orphans
echo "⏳ Waiting 2s before scaling parser..."
sleep 2


echo "🚀 Step 5: Building & Deploying Parser"
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml build --no-cache parser
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml up -d parser --remove-orphans
echo "⏳ Waiting 2s before Crawler..."
sleep 2

echo "🚀 Step 6: Turning Up Dispatcher..."
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml build --no-cache dispatcher
docker compose -f docker/docker-compose.yml -f docker/environments/docker-compose.dev.yml up -d dispatcher --remove-orphans

docker compose -f docker/docker-compose.yml logs -f