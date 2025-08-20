# Step 1: Stop and remove service containers
docker compose -f docker/docker-compose.yml stop
docker compose -f docker/docker-compose.yml rm -f

# Step 2: Remove networks and volumes
docker compose -f docker/docker-compose.yml down -v
