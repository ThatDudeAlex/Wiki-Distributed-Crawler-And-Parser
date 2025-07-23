FROM python:3.13-slim

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/      ./database/
COPY shared/        ./shared/

# service-specific code
COPY components/db_reader/     ./components/db_reader/

# install dependencies
RUN pip install --no-cache-dir -r components/db_reader/requirements.txt

CMD ["python", "-m", "components.db_reader.main"]
