SELECT
    date,
    ticker,
    open,
    high,
    low,
    close,
    adj_close,
    volume
FROM {{ source('raw', 'market_prices') }}