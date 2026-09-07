--tests/int_market_prices_daily_return.sql

SELECT *
FROM {{ ref('int_market_prices') }}
WHERE prev_adj_close IS NOT NULL
AND daily_return != (adj_close / prev_adj_close) - 1