"""Deterministic synthetic data for a payment service provider (PSP).

Same inputs always produce the same rows, so re-running a partition is reproducible.
"""

import random
import zlib
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

COUNTRY_CURRENCY = {
    "AR": "ARS",
    "BR": "BRL",
    "MX": "MXN",
    "US": "USD",
    "ES": "EUR",
    "GB": "GBP",
}
USD_PER_UNIT = {
    "ARS": 0.00085,
    "BRL": 0.18,
    "MXN": 0.055,
    "USD": 1.0,
    "EUR": 1.10,
    "GBP": 1.28,
}
MCC_CATEGORIES = {
    "grocery": "low",
    "restaurants": "low",
    "fashion": "medium",
    "electronics": "medium",
    "travel": "medium",
    "digital_goods": "high",
    "gaming": "high",
    "crypto": "high",
}
CHANNELS = ["ecommerce", "pos", "mobile"]
DECLINE_REASONS = ["insufficient_funds", "do_not_honor", "suspected_fraud", "expired_card"]

REFERENCE_SEED = 42
REFERENCE_AS_OF = date(2026, 8, 31)


@dataclass(frozen=True)
class GeneratorSettings:
    n_customers: int = 2_000
    n_merchants: int = 150
    daily_transactions: int = 4_000
    velocity_bursts_per_day: int = 5
    cross_border_frauds_per_day: int = 20


DEFAULT_SETTINGS = GeneratorSettings()


def _day_seed(day: date) -> int:
    return REFERENCE_SEED * 100_000 + day.toordinal()


def generate_customers(settings: GeneratorSettings = DEFAULT_SETTINGS) -> list[dict]:
    rng = random.Random(REFERENCE_SEED)
    countries = list(COUNTRY_CURRENCY)
    customers = []
    for i in range(1, settings.n_customers + 1):
        is_recent = rng.random() < 0.05
        days_back = rng.randint(1, 30) if is_recent else rng.randint(31, 900)
        customers.append(
            {
                "customer_id": f"C{i:06d}",
                "country": rng.choice(countries),
                "signup_date": REFERENCE_AS_OF - timedelta(days=days_back),
                "kyc_level": rng.choices(["basic", "full"], weights=[0.3, 0.7])[0],
                "segment": rng.choices(["retail", "premium"], weights=[0.85, 0.15])[0],
            }
        )
    return customers


def generate_merchants(settings: GeneratorSettings = DEFAULT_SETTINGS) -> list[dict]:
    rng = random.Random(REFERENCE_SEED + 1)
    categories = list(MCC_CATEGORIES)
    countries = list(COUNTRY_CURRENCY)
    return [
        {
            "merchant_id": f"M{i:04d}",
            "merchant_name": f"Merchant {i:04d}",
            "mcc_category": (category := rng.choice(categories)),
            "country": rng.choice(countries),
            "risk_tier": MCC_CATEGORIES[category],
        }
        for i in range(1, settings.n_merchants + 1)
    ]


def _local_amount(usd_amount: float, currency: str) -> float:
    return round(usd_amount / USD_PER_UNIT[currency], 2)


def _timestamp(day: date, seconds: int) -> datetime:
    return datetime.combine(day, time.min, tzinfo=UTC) + timedelta(seconds=seconds)


def generate_day(
    day: date,
    customers: list[dict],
    merchants: list[dict],
    settings: GeneratorSettings = DEFAULT_SETTINGS,
) -> tuple[list[dict], list[dict]]:
    """Return (transactions, chargebacks) for a single business day."""
    rng = random.Random(_day_seed(day))
    high_risk_merchants = [m for m in merchants if m["risk_tier"] == "high"]
    countries = list(COUNTRY_CURRENCY)
    transactions: list[dict] = []
    fraud_ids: set[str] = set()

    def add_txn(customer: dict, merchant: dict, ts: datetime, usd: float, **overrides) -> dict:
        currency = COUNTRY_CURRENCY[customer["country"]]
        declined = rng.random() < 0.06
        txn = {
            "transaction_id": f"T{day:%Y%m%d}{len(transactions):06d}",
            "customer_id": customer["customer_id"],
            "merchant_id": merchant["merchant_id"],
            "transaction_ts": ts,
            "amount": _local_amount(usd, currency),
            "currency": currency,
            "channel": rng.choice(CHANNELS),
            "card_present": False,
            "ip_country": customer["country"],
            "device_id": f"D{zlib.crc32(customer['customer_id'].encode()) % 10**8:08d}",
            "status": "declined" if declined else "approved",
            "decline_reason": rng.choice(DECLINE_REASONS) if declined else None,
        }
        txn["card_present"] = txn["channel"] == "pos"
        txn.update(overrides)
        transactions.append(txn)
        return txn

    for _ in range(settings.daily_transactions):
        customer = rng.choice(customers)
        traveling = rng.random() < 0.03
        add_txn(
            customer,
            rng.choice(merchants),
            _timestamp(day, rng.randint(0, 86_399)),
            min(rng.lognormvariate(3.5, 1.0), 1_200.0),
            ip_country=rng.choice(countries) if traveling else customer["country"],
        )

    for _ in range(settings.velocity_bursts_per_day):
        customer = rng.choice(customers)
        start = rng.randint(0, 86_399 - 1_800)
        foreign = rng.choice([c for c in countries if c != customer["country"]])
        for _ in range(rng.randint(6, 10)):
            txn = add_txn(
                customer,
                rng.choice(high_risk_merchants),
                _timestamp(day, start + rng.randint(0, 1_800)),
                rng.uniform(50, 400),
                channel="ecommerce",
                card_present=False,
                ip_country=foreign,
                device_id=f"D{rng.randint(0, 10**8):08d}",
                status="approved",
                decline_reason=None,
            )
            fraud_ids.add(txn["transaction_id"])

    for _ in range(settings.cross_border_frauds_per_day):
        customer = rng.choice(customers)
        txn = add_txn(
            customer,
            rng.choice(merchants),
            _timestamp(day, rng.randint(0, 86_399)),
            rng.uniform(1_500, 5_000),
            channel="ecommerce",
            card_present=False,
            ip_country=rng.choice([c for c in countries if c != customer["country"]]),
            status="approved",
            decline_reason=None,
        )
        fraud_ids.add(txn["transaction_id"])

    chargebacks = []
    for txn in transactions:
        if txn["status"] != "approved":
            continue
        is_fraud = txn["transaction_id"] in fraud_ids
        if (is_fraud and rng.random() < 0.7) or (not is_fraud and rng.random() < 0.003):
            chargebacks.append(
                {
                    "chargeback_id": f"CB{txn['transaction_id'][1:]}",
                    "transaction_id": txn["transaction_id"],
                    "reason_code": "fraud"
                    if is_fraud
                    else rng.choice(["product_not_received", "duplicate", "not_as_described"]),
                    "amount": txn["amount"],
                    "currency": txn["currency"],
                    "reported_at": txn["transaction_ts"] + timedelta(days=rng.randint(3, 45)),
                }
            )

    transactions.sort(key=lambda t: t["transaction_ts"])
    return transactions, chargebacks
