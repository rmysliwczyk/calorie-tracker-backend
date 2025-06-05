FROM python:3-slim

WORKDIR /

COPY app /app

COPY alembic.ini .
COPY ".env" .
COPY "requirements.txt" .
RUN pip install -r requirements.txt

COPY "initialize_database.py" .
RUN python3 initialize_database.py

ENTRYPOINT [ "fastapi", "dev", "--host", "0.0.0.0", "--port", "8001" ]