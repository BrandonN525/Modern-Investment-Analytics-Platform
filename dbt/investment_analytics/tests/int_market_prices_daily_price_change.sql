--tests/int_market_prices_daily_price_change.sql

SELECT *
FROM {{ ref('int_market_prices') }}
WHERE prev_adj_close IS NOT NULL
AND daily_price_change != adj_close - prev_adj_close