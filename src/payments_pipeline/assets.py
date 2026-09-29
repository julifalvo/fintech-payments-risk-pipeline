from datetime import date

import dagster as dg
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

from payments_pipeline.config import DBT_PROJECT_DIR, LANDING_DIR, PIPELINE_START_DATE
from payments_pipeline.ingestion import land_daily_partition, land_reference_data

daily_partitions = dg.DailyPartitionsDefinition(start_date=PIPELINE_START_DATE)

dbt_project = DbtProject(project_dir=DBT_PROJECT_DIR)
dbt_project.prepare_if_dev()


@dg.multi_asset(
    specs=[
        dg.AssetSpec("raw_customers", group_name="landing", kinds={"parquet"}),
        dg.AssetSpec("raw_merchants", group_name="landing", kinds={"parquet"}),
    ],
    description="Reference snapshot of customers and merchants (full overwrite).",
)
def reference_data(context: dg.AssetExecutionContext):
    counts = land_reference_data(LANDING_DIR)
    for name, rows in counts.items():
        yield dg.MaterializeResult(asset_key=f"raw_{name}", metadata={"row_count": rows})


@dg.multi_asset(
    specs=[
        dg.AssetSpec("raw_transactions", group_name="landing", kinds={"parquet"}),
        dg.AssetSpec("raw_chargebacks", group_name="landing", kinds={"parquet"}),
    ],
    partitions_def=daily_partitions,
    description="One Hive partition per business day (dt=YYYY-MM-DD), idempotent overwrite.",
)
def daily_payments(context: dg.AssetExecutionContext):
    day = date.fromisoformat(context.partition_key)
    counts = land_daily_partition(day, LANDING_DIR)
    for name, rows in counts.items():
        yield dg.MaterializeResult(
            asset_key=f"raw_{name}", metadata={"row_count": rows, "partition": day.isoformat()}
        )


@dbt_assets(manifest=dbt_project.manifest_path)
def payments_dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
