FROM python:3.13-slim

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY shared/    ./shared/

# service-specific code
COPY components/rabbitmq_seeder    ./components/rabbitmq_seeder

RUN pip install --no-cache-dir -r components/rabbitmq_seeder/requirements.txt

CMD ["python", "-m", "components.rabbitmq_seeder.main"]
