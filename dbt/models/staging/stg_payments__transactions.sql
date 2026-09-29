with source as (

    select * from {{ source('landing', 'transactions') }}

),

renamed as (

    select
        transaction_id,
        customer_id,
        merchant_id,
        cast(transaction_ts as timestamp) as transaction_at,
        cast(transaction_ts as date) as transaction_date,
        cast(amount as decimal(18, 2)) as amount,
        upper(currency) as currency,
        lower(channel) as channel,
        card_present,
        upper(ip_country) as ip_country,
        device_id,
        lower(status) as status,
        decline_reason,
        cast(dt as date) as partition_date
    from source

)

select * from renamed
qualify row_number() over (partition by transaction_id order by partition_date desc) = 1
