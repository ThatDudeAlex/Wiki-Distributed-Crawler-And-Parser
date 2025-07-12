FROM python:3.13-slim

# Default to 'development' if not specified
ARG APP_ENV=dev

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/      ./database/
COPY shared/        ./shared/

# service-specific code
COPY components/scheduler/core                ./components/scheduler/core
COPY components/scheduler/services            ./components/scheduler/services

COPY components/scheduler/__init__.py         ./components/scheduler/__init__.py
COPY components/scheduler/Dockerfile          ./components/scheduler/Dockerfile
COPY components/scheduler/main.py             ./components/scheduler/main.py 
COPY components/scheduler/message_handler.py  ./components/scheduler/message_handler.py 
COPY components/scheduler/requirements.txt    ./components/scheduler/requirements.txt 

# Conditionally copy the environment-specific config file and rename it
COPY components/scheduler/configs/scheduler_config.py       ./components/scheduler/configs/scheduler_config.py
COPY components/scheduler/configs/scheduler_${APP_ENV}.yml  ./components/scheduler/configs/config.yml

RUN pip install --no-cache-dir -r components/scheduler/requirements.txt

CMD ["python", "-m", "components.scheduler.main"]
