FROM python:3.13-slim

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY shared/    ./shared/

# service-specific code
COPY seeder/    ./seeder/

RUN pip install --no-cache-dir -r seeder/requirements.txt

CMD ["python", "-m", "seeder.seed_urls"]
