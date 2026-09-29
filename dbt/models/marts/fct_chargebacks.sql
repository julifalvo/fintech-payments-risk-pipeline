with chargebacks as (

    select * from {{ ref('stg_payments__chargebacks') }}

),

transactions as (

    select transaction_id, transaction_at, transaction_date, merchant_id
    from {{ ref('stg_payments__transactions') }}

),

fx_rates as (

    select * from {{ ref('fx_rates') }}

)

select
    cast(chargebacks.chargeback_id as varchar) as chargeback_id,
    cast(chargebacks.transaction_id as varchar) as transaction_id,
    cast(transactions.merchant_id as varchar) as merchant_id,
    cast(transactions.transaction_date as date) as transaction_date,
    cast(chargebacks.reason_code as varchar) as reason_code,
    cast(chargebacks.reason_code = 'fraud' as boolean) as is_fraud_reason,
    cast(chargebacks.amount as decimal(18, 2)) as amount,
    cast(chargebacks.currency as varchar) as currency,
    cast(round(chargebacks.amount * fx_rates.usd_per_unit, 2) as decimal(18, 2)) as amount_usd,
    cast(chargebacks.reported_at as timestamp) as reported_at,
    cast(date_diff('day', transactions.transaction_at, chargebacks.reported_at) as integer)
        as days_to_report
from chargebacks
left join transactions on chargebacks.transaction_id = transactions.transaction_id
left join fx_rates on chargebacks.currency = fx_rates.currency
