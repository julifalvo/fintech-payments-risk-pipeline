{{
    config(
        materialized='incremental',
        unique_key='transaction_id',
        incremental_strategy='delete+insert',
        on_schema_change='fail'
    )
}}

select
    cast(transaction_id as varchar) as transaction_id,
    cast(transaction_date as date) as transaction_date,
    cast(transaction_at as timestamp) as transaction_at,
    cast(customer_id as varchar) as customer_id,
    cast(merchant_id as varchar) as merchant_id,
    cast(amount as decimal(18, 2)) as amount,
    cast(currency as varchar) as currency,
    cast(amount_usd as decimal(18, 2)) as amount_usd,
    cast(channel as varchar) as channel,
    cast(card_present as boolean) as card_present,
    cast(ip_country as varchar) as ip_country,
    cast(is_cross_border as boolean) as is_cross_border,
    cast(status as varchar) as status,
    cast(decline_reason as varchar) as decline_reason,
    cast(customer_txn_count_1h as integer) as customer_txn_count_1h,
    cast(customer_amount_usd_24h as decimal(18, 2)) as customer_amount_usd_24h,
    cast(risk_score as integer) as risk_score,
    cast(risk_level as varchar) as risk_level,
    cast(risk_reasons as varchar) as risk_reasons,
    cast(risk_score >= {{ var('risk_alert_threshold') }} as boolean) as is_risk_alert
from {{ ref('int_transactions__scored') }}

{% if is_incremental() %}
where transaction_date >= (
    select max(transaction_date) - interval {{ var('incremental_lookback_days') }} day
    from {{ this }}
)
{% endif %}
