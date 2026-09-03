--tests/stg_market_prices_positive_prices.sql

SELECT
    date,
    ticker,
    open,
    high,
    low,
    close,
    adj_close
FROM {{ ref('stg_market_prices')}}
WHERE open <= 0 OR high <= 0 OR low <= 0 OR close <= 0 OR adj_close <= 0