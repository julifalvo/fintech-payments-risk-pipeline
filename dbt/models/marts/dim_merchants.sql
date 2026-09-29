select
    cast(merchant_id as varchar) as merchant_id,
    cast(merchant_name as varchar) as merchant_name,
    cast(mcc_category as varchar) as mcc_category,
    cast(country as varchar) as country,
    cast(risk_tier as varchar) as risk_tier
from {{ ref('stg_payments__merchants') }}
