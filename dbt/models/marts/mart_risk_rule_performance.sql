with labeled as (

    select
        transactions.transaction_date,
        transactions.is_risk_alert,
        coalesce(chargebacks.is_fraud_reason, false) as is_confirmed_fraud
    from {{ ref('fct_transactions') }} as transactions
    left join {{ ref('fct_chargebacks') }} as chargebacks
        on transactions.transaction_id = chargebacks.transaction_id
    where transactions.status = 'approved'

),

daily as (

    select
        transaction_date,
        count(*) as approved_txn_count,
        count(*) filter (where is_risk_alert) as alert_count,
        count(*) filter (where is_confirmed_fraud) as confirmed_fraud_count,
        count(*) filter (where is_risk_alert and is_confirmed_fraud) as true_positive_count
    from labeled
    group by 1

)

select
    cast(transaction_date as date) as transaction_date,
    cast(approved_txn_count as integer) as approved_txn_count,
    cast(alert_count as integer) as alert_count,
    cast(confirmed_fraud_count as integer) as confirmed_fraud_count,
    cast(true_positive_count as integer) as true_positive_count,
    cast(true_positive_count / nullif(alert_count, 0) as double) as alert_precision,
    cast(true_positive_count / nullif(confirmed_fraud_count, 0) as double) as fraud_recall
from daily
