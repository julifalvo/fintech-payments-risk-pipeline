from datetime import date

import pyarrow.parquet as pq

from payments_pipeline.generator import GeneratorSettings
from payments_pipeline.ingestion import SCHEMAS, land_daily_partition, land_reference_data

SETTINGS = GeneratorSettings(n_customers=100, n_merchants=10, daily_transactions=200)
DAY = date(2026, 9, 1)


def test_daily_partition_uses_hive_layout(tmp_path):
    land_daily_partition(DAY, tmp_path, SETTINGS)
    for dataset in ("transactions", "chargebacks"):
        assert (tmp_path / dataset / "dt=2026-09-01" / "data.parquet").exists()


def test_rerunning_a_partition_is_idempotent(tmp_path):
    first = land_daily_partition(DAY, tmp_path, SETTINGS)
    second = land_daily_partition(DAY, tmp_path, SETTINGS)
    table = pq.read_table(tmp_path / "transactions" / "dt=2026-09-01" / "data.parquet")

    assert first == second
    assert table.num_rows == first["transactions"]
    assert not list(tmp_path.rglob("*.tmp"))


def test_written_files_match_declared_schemas(tmp_path):
    land_reference_data(tmp_path, SETTINGS)
    land_daily_partition(DAY, tmp_path, SETTINGS)

    assert pq.read_schema(tmp_path / "customers" / "data.parquet").equals(SCHEMAS["customers"])
    assert pq.read_schema(tmp_path / "merchants" / "data.parquet").equals(SCHEMAS["merchants"])
    transactions_file = tmp_path / "transactions" / "dt=2026-09-01" / "data.parquet"
    assert pq.read_schema(transactions_file).equals(SCHEMAS["transactions"])
