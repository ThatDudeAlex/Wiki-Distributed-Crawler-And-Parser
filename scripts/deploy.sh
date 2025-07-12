#!/bin/bash

DEPLOY_ENV=$1

# Get the directory where THIS SCRIPT (deploy.sh) is located
DEPLOY_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SCRIPT_PATH="${DEPLOY_SCRIPT_DIR}/deploy_configs/deploy_env.sh"

if [[ $DEPLOY_ENV == "prod" ]]; then
  docker context use distribute-prod
  sh $SCRIPT_PATH prod
else
  docker context use distribute-dev
  sh $SCRIPT_PATH dev
fi