.PHONY: setup ingest dbt-build pipeline dagster test lint format docs docker-up clean

START ?= 2026-09-01
END ?= 2026-09-07
DBT = cd dbt && uv run dbt

setup:
	uv sync
	uv run pre-commit install

ingest:
	uv run payments ingest --start $(START) --end $(END)

dbt-build:
	$(DBT) build --profiles-dir .

pipeline: ingest dbt-build

dagster:
	uv run dg dev

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

docs:
	$(DBT) docs generate --profiles-dir . && $(DBT) docs serve --profiles-dir . --port 8081

docker-up:
	docker compose up --build

clean:
	rm -rf data dbt/target dbt/logs .dagster_home
