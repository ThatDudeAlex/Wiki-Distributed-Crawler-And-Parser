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