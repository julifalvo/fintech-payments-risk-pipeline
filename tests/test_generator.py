from datetime import date

import pytest

from payments_pipeline.generator import (
    USD_PER_UNIT,
    GeneratorSettings,
    generate_customers,
    generate_day,
    generate_merchants,
)

SETTINGS = GeneratorSettings(n_customers=200, n_merchants=20, daily_transactions=300)
DAY = date(2026, 9, 1)


@pytest.fixture(scope="module")
def reference():
    return generate_customers(SETTINGS), generate_merchants(SETTINGS)


@pytest.fixture(scope="module")
def day_data(reference):
    customers, merchants = reference
    return generate_day(DAY, customers, merchants, SETTINGS)


def test_same_day_is_reproducible(reference, day_data):
    customers, merchants = reference
    assert generate_day(DAY, customers, merchants, SETTINGS) == day_data


def test_different_days_differ(reference, day_data):
    customers, merchants = reference
    other, _ = generate_day(date(2026, 9, 2), customers, merchants, SETTINGS)
    assert [t["amount"] for t in other] != [t["amount"] for t in day_data[0]]


def test_transaction_ids_are_unique(day_data):
    transactions, _ = day_data
    ids = [t["transaction_id"] for t in transactions]
    assert len(ids) == len(set(ids))


def test_transactions_fall_within_the_business_day(day_data):
    transactions, _ = day_data
    assert {t["transaction_ts"].date() for t in transactions} == {DAY}


def test_includes_injected_cross_border_high_amount_fraud(reference, day_data):
    customers, _ = reference
    transactions, _ = day_data
    home = {c["customer_id"]: c["country"] for c in customers}
    suspicious = [
        t
        for t in transactions
        if t["ip_country"] != home[t["customer_id"]]
        and t["amount"] * USD_PER_UNIT[t["currency"]] >= 1_500
    ]
    assert len(suspicious) >= SETTINGS.cross_border_frauds_per_day


def test_chargebacks_only_reference_approved_transactions(day_data):
    transactions, chargebacks = day_data
    approved = {t["transaction_id"] for t in transactions if t["status"] == "approved"}
    assert chargebacks
    assert {c["transaction_id"] for c in chargebacks} <= approved
    assert any(c["reason_code"] == "fraud" for c in chargebacks)


def test_chargebacks_are_reported_after_the_transaction(day_data):
    transactions, chargebacks = day_data
    ts_by_id = {t["transaction_id"]: t["transaction_ts"] for t in transactions}
    assert all(c["reported_at"] > ts_by_id[c["transaction_id"]] for c in chargebacks)
