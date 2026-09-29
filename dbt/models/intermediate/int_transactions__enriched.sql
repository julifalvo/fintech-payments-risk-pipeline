with transactions as (

    select * from {{ ref('stg_payments__transactions') }}

),

customers as (

    select * from {{ ref('stg_payments__customers') }}

),

merchants as (

    select * from {{ ref('stg_payments__merchants') }}

),

fx_rates as (

    select * from {{ ref('fx_rates') }}

)

select
    transactions.transaction_id,
    transactions.customer_id,
    transactions.merchant_id,
    transactions.transaction_at,
    transactions.transaction_date,
    transactions.amount,
    transactions.currency,
    cast(round(transactions.amount * fx_rates.usd_per_unit, 2) as decimal(18, 2)) as amount_usd,
    transactions.channel,
    transactions.card_present,
    transactions.ip_country,
    transactions.device_id,
    transactions.status,
    transactions.decline_reason,
    customers.country as customer_country,
    customers.kyc_level,
    customers.segment as customer_segment,
    date_diff('day', customers.signup_date, transactions.transaction_date) as account_age_days,
    merchants.mcc_category,
    merchants.risk_tier as merchant_risk_tier,
    transactions.ip_country <> customers.country as is_cross_border
from transactions
left join fx_rates on transactions.currency = fx_rates.currency
left join customers on transactions.customer_id = customers.customer_id
left join merchants on transactions.merchant_id = merchants.merchant_id
