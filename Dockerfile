FROM python:3.13-slim-trixie

RUN apt update && apt install -y postgresql postgresql-common-dev python3-dev
WORKDIR /

COPY app /app

COPY alembic.ini .
COPY ".env" .
COPY "requirements.txt" .
RUN pip install setuptools --upgrade
RUN pip install -r requirements.txt

COPY "initialize_database.py" .
RUN python3 initialize_database.py

ENTRYPOINT [ "fastapi", "run", "--host", "0.0.0.0", "--port", "8001" ]
