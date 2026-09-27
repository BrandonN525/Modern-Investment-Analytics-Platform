--tests/fct_market_performance_cumulative_return.sql

SELECT
    date,
    ticker,
    cumulative_return
FROM {{ ref('fct_market_performance') }}
WHERE date = (
    SELECT MIN(date)
    FROM {{ ref('fct_market_performance') }} f2
    WHERE f2.ticker = fct_market_performance.ticker
)
AND ABS(cumulative_return) > 0.000000001