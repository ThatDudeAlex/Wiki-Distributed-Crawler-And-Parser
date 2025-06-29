FROM python:3.13-slim

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/   ./database/
# COPY db/          ./db/

# service-specific code
# COPY db_init/     ./db_init/

RUN pip install --no-cache-dir -r database/db_init/requirements.txt

CMD ["python", "-m", "database.db_init.db_init"]