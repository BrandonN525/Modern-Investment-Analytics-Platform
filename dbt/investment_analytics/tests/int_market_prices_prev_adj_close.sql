--tests/int_market_prices_prev_adj_close.sql

SELECT
    date,
    ticker,
    adj_close,
    prev_adj_close
FROM {{ ref('int_market_prices') }}
WHERE
    (
        date = (
            SELECT min(date)
            FROM {{ ref('int_market_prices') }} i2
            WHERE i2.ticker = int_market_prices.ticker
        )
        AND prev_adj_close IS NOT NULL
    )
    OR
    (
        date != (
            SELECT min(date)
            FROM {{ ref('int_market_prices') }} i2
            WHERE i2.ticker = int_market_prices.ticker
        )
        AND prev_adj_close IS NULL
    )