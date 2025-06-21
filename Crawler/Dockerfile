FROM python:3.13-slim

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY utilities/   ./utilities/
COPY db_models/   ./db_models/
COPY db/          ./db/

COPY config.py    ./config.py

# service-specific code
COPY crawler/     ./crawler/

RUN pip install --no-cache-dir -r crawler/requirements.txt

CMD ["python", "-m", "crawler.crawler"]
