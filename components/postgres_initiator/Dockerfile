FROM python:3.13-slim

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/                ./database
COPY shared/                  ./shared

# service-specific code
COPY components/postgres_initiator   ./components/postgres_initiator

RUN pip install --no-cache-dir -r components/postgres_initiator/requirements.txt

CMD ["python", "-m", "components.postgres_initiator.main"]