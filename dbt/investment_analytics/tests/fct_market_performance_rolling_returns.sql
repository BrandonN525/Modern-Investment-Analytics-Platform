--tests/fct_market_performance_rolling_returns.sql

WITH numbered as (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date) as row_num
    FROM {{ ref('fct_market_performance') }}
)

SELECT
    date,
    ticker,
    rolling_21d_return,
    rolling_63d_return,
    rolling_252d_return
FROM numbered
WHERE 1=1
AND ((row_num <= 21 AND rolling_21d_return IS NOT NULL)
      OR (row_num > 21 AND rolling_21d_return IS NULL)
      OR (row_num <= 63 AND rolling_63d_return IS NOT NULL)
      OR (row_num > 63 AND rolling_63d_return IS NULL)
      OR (row_num <= 252 AND rolling_252d_return IS NOT NULL)
      OR (row_num > 252 AND rolling_252d_return IS NULL))