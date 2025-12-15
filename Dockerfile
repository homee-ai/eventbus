FROM python:3.11.7-slim-bullseye as builder

RUN apt-get update && apt-get install -y \
    curl \
    git \
    openssh-client \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /eventbus

ENV POETRY_HOME=/tmp/poetry
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN which poetry

COPY . .

RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true \
    && poetry install --no-interaction --no-ansi