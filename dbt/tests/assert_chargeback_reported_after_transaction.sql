-- A dispute cannot be raised before the transaction it disputes.
select *
from {{ ref('fct_chargebacks') }}
where days_to_report < 0
