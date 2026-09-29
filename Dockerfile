FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PAYMENTS_DATA_DIR=/data \
    DAGSTER_HOME=/opt/dagster/home

WORKDIR /app

# Dependencies first so code changes don't invalidate this layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev \
    && mkdir -p "$DAGSTER_HOME" \
    && cd dbt && dbt parse --profiles-dir .

RUN useradd --create-home --uid 1000 pipeline \
    && mkdir -p /data \
    && chown -R pipeline:pipeline /app /data "$DAGSTER_HOME"
USER pipeline

EXPOSE 3000
CMD ["dagster", "dev", "-h", "0.0.0.0", "-p", "3000"]
