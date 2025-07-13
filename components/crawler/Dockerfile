FROM python:3.13-slim

# Default to 'dev' if not specified
ARG APP_ENV=dev 

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/      ./database/
COPY shared/        ./shared/

# service-specific code
COPY components/crawler/core                ./components/crawler/core
COPY components/crawler/services            ./components/crawler/services
COPY components/crawler/types               ./components/crawler/types
COPY components/crawler/__init__.py         ./components/crawler/__init__.py
COPY components/crawler/Dockerfile          ./components/crawler/Dockerfile
COPY components/crawler/main.py             ./components/crawler/main.py 
COPY components/crawler/requirements.txt    ./components/crawler/requirements.txt 

# Conditionally copy the environment-specific config file and rename it
COPY components/crawler/configs/crawler_config.py       ./components/crawler/configs/crawler_config.py
COPY components/crawler/configs/crawler_${APP_ENV}.yml  ./components/crawler/configs/config.yml

RUN pip install --no-cache-dir -r components/crawler/requirements.txt

CMD ["python", "-m", "components.crawler.main"]
