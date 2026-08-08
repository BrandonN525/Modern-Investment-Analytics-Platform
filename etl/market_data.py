import yfinance as yf
import pandas as pd
from pathlib import Path
import duckdb

#Project Paths

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / 'data'
DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_PATH = DATABASE_DIR / "investment_analytics.duckdb"

#Configuration

etfs = ['SPY', 'QQQ', 'IWM', 'VTI', 'VXUS', 'BND']

#Extract - Download market data from Yahoo Finance

data = yf.download(etfs, start='2020-01-01', end='2026-01-01')

#Transform - Normalize and standardize market data

df_long = data.stack(level='Ticker', future_stack=True).reset_index()

df_long = df_long.rename(columns={
    'Date': 'date',
    'Ticker': 'ticker',
    'Close': 'close',
    'High': 'high',
    'Low': 'low',
    'Open': 'open',
    'Volume': 'volume'
})

df_long['date'] = pd.to_datetime(df_long['date'])
df_long['ticker'] = df_long['ticker'].astype('string')

price_cols = ['open', 'high', 'low', 'close']

df_long[price_cols] = df_long[price_cols].astype('float64')
df_long['volume'] = df_long['volume'].astype('Int64')

#Data Quality Checks

assert df_long['ticker'].notna().all()
assert df_long['date'].notna().all()
assert df_long['close'].notna().all()

assert df_long.duplicated(['date', 'ticker']).sum() == 0

assert (df_long["volume"] >= 0).all()

assert (df_long['high'] >= df_long['low']).all()
assert (df_long['high'] >= df_long['open']).all()
assert (df_long['high'] >= df_long['close']).all()
assert (df_long['low'] <= df_long['open']).all()
assert (df_long['low'] <= df_long['close']).all()

expected_tickers = {'BND', 'IWM', 'QQQ', 'SPY', 'VTI', 'VXUS'}

actual_tickers = set(df_long['ticker'].unique())
missing_tickers = expected_tickers - actual_tickers

if missing_tickers:
    raise ValueError(f'Missing tickers: {missing_tickers}')

assert (df_long['volume'] >= 0).all()
assert (df_long['open'] > 0).all()
assert (df_long['high'] > 0).all()
assert (df_long['low'] > 0).all()
assert (df_long['close'] > 0).all()

#Load - Write validated data to DuckDB

with duckdb.connect(DATABASE_PATH) as con:
    con.execute("""
        CREATE OR REPLACE TABLE raw_market_prices AS
        SELECT *
        FROM df_long
    """)

    print(
        con.execute("""
            SELECT *
            FROM raw_market_prices
            LIMIT 10
        """).fetchdf()
    )

    print(
        con.execute("""
            SELECT
                COUNT(*) AS row_count,
                COUNT(DISTINCT ticker) AS ticker_count,
                MIN(date) AS earliest_date,
                MAX(date) AS latest_date
            FROM raw_market_prices
        """).fetchdf()
    )