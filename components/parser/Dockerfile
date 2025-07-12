FROM python:3.13-slim

# Default to 'dev' if not specified
ARG APP_ENV=dev 

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/      ./database/
COPY shared/        ./shared/

# service-specific code
COPY components/parser/services       ./components/parser/services
COPY components/parser/core           ./components/parser/core

COPY components/parser/__init__.py         ./components/parser/__init__.py
COPY components/parser/Dockerfile          ./components/parser/Dockerfile
COPY components/parser/main.py             ./components/parser/main.py 
COPY components/parser/message_handler.py  ./components/parser/message_handler.py 
COPY components/parser/requirements.txt    ./components/parser/requirements.txt 

# Conditionally copy the environment-specific config file and rename it
COPY components/parser/configs/parser_config.py       ./components/parser/configs/parser_config.py
COPY components/parser/configs/app_configs.py       ./components/parser/configs/app_configs.py
COPY components/parser/configs/parser_${APP_ENV}.yml  ./components/parser/configs/config.yml

RUN pip install --no-cache-dir -r components/parser/requirements.txt

CMD ["python", "-m", "components.parser.main"]
