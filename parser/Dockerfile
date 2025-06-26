FROM python:3.13-slim

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/      ./database/
COPY shared/        ./shared/

# service-specific code
COPY parser/        ./parser/

RUN pip install --no-cache-dir -r parser/requirements.txt

CMD ["python", "-m", "parser.parser"]
