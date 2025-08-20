docker container stop $(docker container ls -aq) 2>/dev/null
docker system prune -a --volumes --force
