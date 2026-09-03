--tests/stg_market_prices_valid_ohlc.sql

SELECT
    date,
    ticker,
    high,
    low,
    open,
    close
FROM {{ ref('stg_market_prices')}}
WHERE (high < low) OR (high < open) OR (high < close) OR (open < low) OR (close < low)