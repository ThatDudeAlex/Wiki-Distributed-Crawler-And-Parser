FROM python:3.13-slim

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/      ./database/
COPY shared/        ./shared/

# service-specific code
COPY components/db_writer/     ./components/db_writer/

RUN pip install --no-cache-dir -r components/db_writer/requirements.txt

CMD ["python", "-m", "components.db_writer.main"]
