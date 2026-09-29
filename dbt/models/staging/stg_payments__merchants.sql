select
    merchant_id,
    merchant_name,
    lower(mcc_category) as mcc_category,
    upper(country) as country,
    lower(risk_tier) as risk_tier
from {{ source('landing', 'merchants') }}
