import argparse
import logging
from datetime import date, timedelta

from payments_pipeline.config import LANDING_DIR
from payments_pipeline.ingestion import land_daily_partition, land_reference_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Land synthetic PSP data into the Parquet lake.")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="Land reference data and a range of daily partitions.")
    ingest.add_argument("--start", type=date.fromisoformat, required=True)
    ingest.add_argument("--end", type=date.fromisoformat, help="Inclusive. Defaults to --start.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    end = args.end or args.start
    if end < args.start:
        parser.error("--end must be on or after --start")

    land_reference_data(LANDING_DIR)
    day = args.start
    while day <= end:
        land_daily_partition(day, LANDING_DIR)
        day += timedelta(days=1)


if __name__ == "__main__":
    main()
