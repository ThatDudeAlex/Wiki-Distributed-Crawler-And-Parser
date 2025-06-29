FROM python:3.13-slim

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/      ./database/
COPY shared/        ./shared/

# service-specific code
COPY database_service/        ./database_service/

RUN pip install --no-cache-dir -r database_service/requirements.txt

CMD ["python", "-m", "database_service.db_service"]
