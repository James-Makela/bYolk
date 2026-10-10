FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.22 /uv /uvx /bin/

ENV PYTHONUNBUFFERED 1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /code

COPY pyproject.toml uv.lock ./
ARG UV_SYNC_ARGS="--no-dev"
RUN uv sync --locked ${UV_SYNC_ARGS}

COPY . .

ENTRYPOINT ["/code/entrypoint.sh"]
