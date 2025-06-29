FROM python:3.13-slim

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/      ./database/
COPY shared/        ./shared/

# service-specific code
COPY components/crawler/     ./components/crawler/

RUN pip install --no-cache-dir -r components/crawler/requirements.txt

CMD ["python", "-m", "components.crawler.main"]
