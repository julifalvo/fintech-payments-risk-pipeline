with transactions as (

    select * from {{ ref('fct_transactions') }}

),

chargebacks as (

    select transaction_id from {{ ref('fct_chargebacks') }}

),

merchants as (

    select * from {{ ref('dim_merchants') }}

),

daily as (

    select
        transactions.transaction_date,
        transactions.merchant_id,
        count(*) as txn_count,
        count(*) filter (where transactions.status = 'approved') as approved_count,
        coalesce(sum(transactions.amount_usd) filter (where transactions.status = 'approved'), 0)
            as tpv_usd,
        count(chargebacks.transaction_id) as chargeback_count,
        count(*) filter (where transactions.is_risk_alert) as risk_alert_count
    from transactions
    left join chargebacks on transactions.transaction_id = chargebacks.transaction_id
    group by 1, 2

)

select
    cast(daily.transaction_date as date) as transaction_date,
    cast(daily.merchant_id as varchar) as merchant_id,
    cast(merchants.mcc_category as varchar) as mcc_category,
    cast(merchants.risk_tier as varchar) as merchant_risk_tier,
    cast(daily.txn_count as integer) as txn_count,
    cast(daily.approved_count as integer) as approved_count,
    cast(daily.tpv_usd as decimal(18, 2)) as tpv_usd,
    cast(daily.approved_count / daily.txn_count as double) as approval_rate,
    cast(daily.chargeback_count as integer) as chargeback_count,
    cast(daily.chargeback_count / nullif(daily.approved_count, 0) as double) as chargeback_rate,
    cast(daily.risk_alert_count as integer) as risk_alert_count
from daily
left join merchants on daily.merchant_id = merchants.merchant_id
