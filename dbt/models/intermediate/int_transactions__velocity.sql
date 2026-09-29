select
    *,
    count(*) over customer_last_hour as customer_txn_count_1h,
    sum(amount_usd) over customer_last_24h as customer_amount_usd_24h
from {{ ref('int_transactions__enriched') }}
window
    customer_last_hour as (
        partition by customer_id
        order by transaction_at
        range between interval 1 hour preceding and current row
    ),
    customer_last_24h as (
        partition by customer_id
        order by transaction_at
        range between interval 24 hours preceding and current row
    )
