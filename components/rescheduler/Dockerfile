FROM python:3.13-slim

# Default to 'development' if not specified
ARG APP_ENV=dev

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/      ./database/
COPY shared/        ./shared/

# service-specific code
COPY components/rescheduler/services           ./components/rescheduler/services
COPY components/rescheduler/__init__.py        ./components/rescheduler/__init__.py
COPY components/rescheduler/Dockerfile         ./components/rescheduler/Dockerfile
COPY components/rescheduler/main.py            ./components/rescheduler/main.py 
COPY components/rescheduler/requirements.txt   ./components/rescheduler/requirements.txt 

# Conditionally copy the environment-specific config file and rename it
COPY components/rescheduler/configs/rescheduler_config.py       ./components/rescheduler/configs/rescheduler_config.py
COPY components/rescheduler/configs/rescheduler_${APP_ENV}.yml  ./components/rescheduler/configs/config.yml

RUN pip install --no-cache-dir -r components/rescheduler/requirements.txt

CMD ["python", "-m", "components.rescheduler.main"]
