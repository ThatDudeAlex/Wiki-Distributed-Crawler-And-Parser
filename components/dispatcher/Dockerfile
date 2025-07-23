FROM python:3.13-slim

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/      ./database/
COPY shared/        ./shared/

# service-specific code
COPY components/dispatcher           ./components/dispatcher

# install dependencies
RUN pip install --no-cache-dir -r components/dispatcher/requirements.txt

CMD ["python", "-m", "components.dispatcher.main"]
