--tests/stg_market_prices_nonnegative_volume.sql

SELECT
    date,
    ticker,
    volume
FROM {{ ref('stg_market_prices')}}
WHERE volume < 0