# pull official base image
FROM python:3.11-slim

# set work directory
WORKDIR /app

# install python to be able to install psycopg2
RUN apt update \
    && apt-get -y install libpq-dev

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev
COPY . .

