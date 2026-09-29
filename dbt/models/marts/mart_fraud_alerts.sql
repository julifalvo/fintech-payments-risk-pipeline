with alerts as (

    select * from {{ ref('fct_transactions') }}
    where is_risk_alert

),

chargebacks as (

    select transaction_id, is_fraud_reason from {{ ref('fct_chargebacks') }}

)

select
    cast(alerts.transaction_id as varchar) as transaction_id,
    cast(alerts.transaction_at as timestamp) as transaction_at,
    cast(alerts.transaction_date as date) as transaction_date,
    cast(alerts.customer_id as varchar) as customer_id,
    cast(alerts.merchant_id as varchar) as merchant_id,
    cast(alerts.amount_usd as decimal(18, 2)) as amount_usd,
    cast(alerts.status as varchar) as status,
    cast(alerts.risk_score as integer) as risk_score,
    cast(alerts.risk_level as varchar) as risk_level,
    cast(alerts.risk_reasons as varchar) as risk_reasons,
    cast(coalesce(chargebacks.is_fraud_reason, false) as boolean) as is_confirmed_fraud
from alerts
left join chargebacks on alerts.transaction_id = chargebacks.transaction_id
