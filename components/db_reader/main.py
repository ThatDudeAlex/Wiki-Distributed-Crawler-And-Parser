from fastapi import FastAPI
from components.db_reader.services.reader_service import DbReaderService

app = FastAPI()
service = DbReaderService(app)

if __name__ == "__main__":
    service.run()
