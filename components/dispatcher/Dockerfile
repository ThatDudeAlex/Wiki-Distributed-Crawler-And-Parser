FROM python:3.13-slim

# Default to 'development' if not specified
ARG APP_ENV=development 

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/      ./database/
COPY shared/        ./shared/

# service-specific code
COPY components/dispatcher/                   ./components/dispatcher/
COPY components/dispatcher/services           ./components/dispatcher/services
COPY components/dispatcher/types              ./components/dispatcher/types
COPY components/dispatcher/__init__.py        ./components/dispatcher/__init__.py
COPY components/dispatcher/Dockerfile         ./components/dispatcher/Dockerfile
COPY components/dispatcher/main.py            ./components/dispatcher/main.py 
COPY components/dispatcher/requirements.txt   ./components/dispatcher/requirements.txt 

# Conditionally copy the environment-specific config file and rename it
COPY components/dispatcher/configs/dispatcher_config.py       ./components/dispatcher/configs/dispatcher_config.py
COPY components/dispatcher/configs/dispatcher_${APP_ENV}.yml  ./components/dispatcher/configs/config.yml

RUN pip install --no-cache-dir -r components/dispatcher/requirements.txt

CMD ["python", "-m", "components.dispatcher.main"]
