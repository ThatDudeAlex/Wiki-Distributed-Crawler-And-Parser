FROM python:3.13-slim

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/      ./database/
COPY shared/        ./shared/

# service-specific code
COPY components/parser       ./components/parser

# install dependencies
RUN pip install --no-cache-dir -r components/parser/requirements.txt

CMD ["python", "-m", "components.parser.main"]
