with source as (

    select * from {{ source('landing', 'chargebacks') }}

),

renamed as (

    select
        chargeback_id,
        transaction_id,
        lower(reason_code) as reason_code,
        cast(amount as decimal(18, 2)) as amount,
        upper(currency) as currency,
        cast(reported_at as timestamp) as reported_at,
        cast(dt as date) as partition_date
    from source

)

select * from renamed
qualify row_number() over (partition by chargeback_id order by partition_date desc) = 1
