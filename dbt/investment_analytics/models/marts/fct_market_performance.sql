WITH rolling_return AS ( 
    SELECT
        date,
        ticker,
        adj_close,
        daily_price_change,
        daily_return,
        log_return,
        FIRST_VALUE(adj_close) OVER (PARTITION BY ticker ORDER BY date) as first_adj_close,
        LAG(adj_close, 21) OVER (PARTITION BY ticker ORDER BY date) as adj_close_21_days_ago,
        LAG(adj_close, 63) OVER (PARTITION BY ticker ORDER BY date) as adj_close_63_days_ago,
        LAG(adj_close, 252) OVER (PARTITION BY ticker ORDER BY date) as adj_close_252_days_ago
    FROM {{ ref('int_market_prices') }}
)

SELECT
    date,
    ticker,
    adj_close,
    daily_price_change,
    daily_return,
    log_return,
    (adj_close / first_adj_close) - 1 as cumulative_return,
    (adj_close / adj_close_21_days_ago) - 1 as rolling_21d_return,
    (adj_close / adj_close_63_days_ago) - 1 as rolling_63d_return,
    (adj_close / adj_close_252_days_ago) - 1 as rolling_252d_return,
    STDDEV_SAMP(log_return) OVER (PARTITION BY ticker ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) * SQRT(252) as rolling_21d_volatility,
    STDDEV_SAMP(log_return) OVER (PARTITION BY ticker ORDER BY date ROWS BETWEEN 62 PRECEDING AND CURRENT ROW) * SQRT(252) as rolling_63d_volatility,
    STDDEV_SAMP(log_return) OVER (PARTITION BY ticker ORDER BY date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) * SQRT(252) as rolling_252d_volatility
FROM rolling_return