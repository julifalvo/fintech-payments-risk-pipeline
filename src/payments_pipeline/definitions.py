import dagster as dg
from dagster_dbt import DbtCliResource

from payments_pipeline.assets import (
    daily_partitions,
    daily_payments,
    dbt_project,
    payments_dbt_models,
    reference_data,
)

ingest_job = dg.define_asset_job(
    "ingest_daily_payments",
    selection=dg.AssetSelection.assets(daily_payments),
    partitions_def=daily_partitions,
)
reference_job = dg.define_asset_job(
    "refresh_reference_data", selection=dg.AssetSelection.assets(reference_data)
)
transform_job = dg.define_asset_job(
    "build_warehouse", selection=dg.AssetSelection.assets(payments_dbt_models)
)

defs = dg.Definitions(
    assets=[reference_data, daily_payments, payments_dbt_models],
    jobs=[ingest_job, reference_job, transform_job],
    schedules=[
        dg.build_schedule_from_partitioned_job(ingest_job, hour_of_day=1),
        dg.ScheduleDefinition(job=reference_job, cron_schedule="30 0 * * *"),
        dg.ScheduleDefinition(job=transform_job, cron_schedule="0 2 * * *"),
    ],
    resources={"dbt": DbtCliResource(project_dir=dbt_project)},
)
