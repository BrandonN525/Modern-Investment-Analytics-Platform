WITH prev_adj_cls AS
(
    SELECT
    date,
    ticker,
    open,
    high,
    low,
    close,
    adj_close,
    volume,
    LAG(adj_close) OVER (PARTITION BY ticker ORDER BY date) as prev_adj_close
    FROM {{ ref('stg_market_prices') }}
)

SELECT
    date,
    ticker,
    open,
    high,
    low,
    close,
    adj_close,
    volume,
    prev_adj_close,
    adj_close - prev_adj_close as daily_price_change,
    (adj_close / prev_adj_close) - 1 as daily_return,
    LN(adj_close / prev_adj_close) as log_return
FROM prev_adj_cls