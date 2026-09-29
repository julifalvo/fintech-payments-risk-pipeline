select
    customer_id,
    upper(country) as country,
    signup_date,
    lower(kyc_level) as kyc_level,
    lower(segment) as segment
from {{ source('landing', 'customers') }}
