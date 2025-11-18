# Build stage
FROM python:3.12.2-slim-bullseye as builder

WORKDIR /app
COPY . .

# Install Poetry
ENV POETRY_HOME=/tmp/poetry
ENV PATH=$POETRY_HOME/bin:$PATH
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry


# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

CMD ["eventbus-cli", "--help"]