select
    cast(customer_id as varchar) as customer_id,
    cast(country as varchar) as country,
    cast(signup_date as date) as signup_date,
    cast(kyc_level as varchar) as kyc_level,
    cast(segment as varchar) as segment
from {{ ref('stg_payments__customers') }}
