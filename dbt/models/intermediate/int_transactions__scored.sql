with flagged as (

    select
        *,
        coalesce(amount_usd >= {{ var('high_amount_usd') }}, false) as flag_high_amount,
        coalesce(customer_txn_count_1h >= {{ var('velocity_txn_threshold') }}, false) as flag_velocity,
        coalesce(is_cross_border, false) as flag_cross_border,
        coalesce(account_age_days < {{ var('new_account_days') }}, false) as flag_new_account,
        coalesce(merchant_risk_tier = 'high', false) as flag_high_risk_merchant
    from {{ ref('int_transactions__velocity') }}

),

scored as (

    select
        *,
        35 * cast(flag_high_amount as integer)
        + 30 * cast(flag_velocity as integer)
        + 15 * cast(flag_cross_border as integer)
        + 10 * cast(flag_new_account as integer)
        + 10 * cast(flag_high_risk_merchant as integer) as risk_score
    from flagged

)

select
    *,
    case
        when risk_score >= 70 then 'high'
        when risk_score >= {{ var('risk_alert_threshold') }} then 'medium'
        else 'low'
    end as risk_level,
    concat_ws(
        ', ',
        case when flag_high_amount then 'high_amount' end,
        case when flag_velocity then 'velocity' end,
        case when flag_cross_border then 'cross_border' end,
        case when flag_new_account then 'new_account' end,
        case when flag_high_risk_merchant then 'high_risk_merchant' end
    ) as risk_reasons
from scored
