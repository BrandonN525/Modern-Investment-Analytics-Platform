--tests/fct_market_performance_volatility.sql

WITH numbered as (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date) as row_num
    FROM {{ ref('fct_market_performance') }}
)

SELECT
    date,
    ticker,
    rolling_21d_volatility,
    rolling_63d_volatility,
    rolling_252d_volatility
FROM numbered
WHERE 1=1
AND ((row_num <= 21 AND rolling_21d_volatility IS NOT NULL)
      OR (row_num > 21 AND rolling_21d_volatility IS NULL)
      OR (row_num <= 63 AND rolling_63d_volatility IS NOT NULL)
      OR (row_num > 63 AND rolling_63d_volatility IS NULL)
      OR (row_num <= 252 AND rolling_252d_volatility IS NOT NULL)
      OR (row_num > 252 AND rolling_252d_volatility IS NULL))