FROM python:3.12.2-slim-bullseye AS builder
LABEL maintainer="ben.liu@homee.ai"

RUN apt-get update && apt-get install -y \
    curl \
    git \
    openssh-client \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

ENV POETRY_HOME=/tmp/poetry
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN which poetry

RUN mkdir -p ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

COPY . .
RUN --mount=type=ssh \
    poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

FROM python:3.12.2-slim-bullseye AS runtime
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app
CMD ["eventbus-cli", "--help"]