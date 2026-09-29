import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt"

DATA_DIR = Path(os.getenv("PAYMENTS_DATA_DIR", PROJECT_ROOT / "data")).resolve()
LANDING_DIR = DATA_DIR / "landing"
DUCKDB_PATH = Path(os.getenv("DUCKDB_PATH", DATA_DIR / "warehouse" / "payments.duckdb")).resolve()
# DuckDB does not create missing parent directories.
DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)

# dbt reads these through env_var() in profiles.yml and sources.yml.
os.environ.setdefault("LANDING_DIR", LANDING_DIR.as_posix())
os.environ.setdefault("DUCKDB_PATH", DUCKDB_PATH.as_posix())

PIPELINE_START_DATE = os.getenv("PIPELINE_START_DATE", "2026-09-01")
