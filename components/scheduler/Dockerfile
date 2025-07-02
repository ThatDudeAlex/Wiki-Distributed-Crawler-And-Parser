FROM python:3.13-slim

WORKDIR /app

# shared code
COPY requirements-common.txt  ./requirements-common.txt
COPY database/      ./database/
COPY shared/        ./shared/

# service-specific code
COPY components/scheduler/        ./components/scheduler/

RUN pip install --no-cache-dir -r components/scheduler/requirements.txt

CMD ["python", "-m", "components.scheduler.main"]
