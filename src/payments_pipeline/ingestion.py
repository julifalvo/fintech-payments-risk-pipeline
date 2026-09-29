"""Land raw data as Parquet in a Hive-partitioned layout.

Each write replaces its target file atomically, so re-running a day is idempotent.
"""

import logging
import os
from datetime import date
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from payments_pipeline.generator import (
    DEFAULT_SETTINGS,
    GeneratorSettings,
    generate_customers,
    generate_day,
    generate_merchants,
)

logger = logging.getLogger(__name__)

TS = pa.timestamp("us", tz="UTC")

SCHEMAS = {
    "customers": pa.schema(
        [
            ("customer_id", pa.string()),
            ("country", pa.string()),
            ("signup_date", pa.date32()),
            ("kyc_level", pa.string()),
            ("segment", pa.string()),
        ]
    ),
    "merchants": pa.schema(
        [
            ("merchant_id", pa.string()),
            ("merchant_name", pa.string()),
            ("mcc_category", pa.string()),
            ("country", pa.string()),
            ("risk_tier", pa.string()),
        ]
    ),
    "transactions": pa.schema(
        [
            ("transaction_id", pa.string()),
            ("customer_id", pa.string()),
            ("merchant_id", pa.string()),
            ("transaction_ts", TS),
            ("amount", pa.float64()),
            ("currency", pa.string()),
            ("channel", pa.string()),
            ("card_present", pa.bool_()),
            ("ip_country", pa.string()),
            ("device_id", pa.string()),
            ("status", pa.string()),
            ("decline_reason", pa.string()),
        ]
    ),
    "chargebacks": pa.schema(
        [
            ("chargeback_id", pa.string()),
            ("transaction_id", pa.string()),
            ("reason_code", pa.string()),
            ("amount", pa.float64()),
            ("currency", pa.string()),
            ("reported_at", TS),
        ]
    ),
}


def _write(rows: list[dict], dataset: str, path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows, schema=SCHEMAS[dataset])
    tmp = path.with_suffix(".parquet.tmp")
    pq.write_table(table, tmp, compression="zstd")
    os.replace(tmp, path)
    logger.info("Wrote %s rows to %s", table.num_rows, path)
    return table.num_rows


def land_reference_data(
    landing_dir: Path, settings: GeneratorSettings = DEFAULT_SETTINGS
) -> dict[str, int]:
    return {
        "customers": _write(
            generate_customers(settings), "customers", landing_dir / "customers" / "data.parquet"
        ),
        "merchants": _write(
            generate_merchants(settings), "merchants", landing_dir / "merchants" / "data.parquet"
        ),
    }


def land_daily_partition(
    day: date, landing_dir: Path, settings: GeneratorSettings = DEFAULT_SETTINGS
) -> dict[str, int]:
    transactions, chargebacks = generate_day(
        day, generate_customers(settings), generate_merchants(settings), settings
    )
    partition = f"dt={day.isoformat()}"
    return {
        "transactions": _write(
            transactions,
            "transactions",
            landing_dir / "transactions" / partition / "data.parquet",
        ),
        "chargebacks": _write(
            chargebacks,
            "chargebacks",
            landing_dir / "chargebacks" / partition / "data.parquet",
        ),
    }
