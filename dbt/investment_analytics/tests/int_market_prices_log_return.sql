--tests/int_market_prices_log_return.sql

SELECT
    date,
    ticker,
    adj_close,
    prev_adj_close,
    log_return
FROM {{ ref('int_market_prices') }}
WHERE prev_adj_close IS NOT NULL
AND (
    log_return is NULL
    OR ABS(
        log_return - LN(adj_close / prev_adj_close)
    ) > 0.000000001
)