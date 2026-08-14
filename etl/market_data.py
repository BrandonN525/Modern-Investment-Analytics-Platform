import yfinance as yf
import pandas as pd
from pathlib import Path
import duckdb
from validation import validate_market_data

#Project Paths

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / 'data'
DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "investment_analytics.duckdb"

#Configuration

etfs = ['SPY', 'QQQ', 'IWM', 'VTI', 'VXUS', 'VT', 'BND']
expected_tickers = {'BND', 'IWM', 'QQQ', 'SPY', 'VTI', 'VXUS', 'VT'}

#Extract - Download market data from Yahoo Finance

def extract_market_data() -> pd.DataFrame:
    data = yf.download(etfs, start='2020-01-01', end='2026-01-01', auto_adjust=False)
    return data

#Transform - Normalize and standardize market data

def transform_market_data(data: pd.DataFrame) -> pd.DataFrame:
    df_long = data.stack(level='Ticker', future_stack=True).reset_index()

    df_long = df_long.rename(columns={
        'Date': 'date',
        'Ticker': 'ticker',
        'Close': 'close',
        'Adj Close': 'adj_close',
        'High': 'high',
        'Low': 'low',
        'Open': 'open',
        'Volume': 'volume'
    })

    df_long['date'] = pd.to_datetime(df_long['date'])
    df_long['ticker'] = df_long['ticker'].astype('string')

    price_cols = ['open', 'high', 'low', 'close', 'adj_close']

    df_long[price_cols] = df_long[price_cols].astype('float64').round(6)
    df_long['volume'] = df_long['volume'].astype('Int64')

    return df_long

#Load - Write validated data to DuckDB

def load_market_data(df: pd.DataFrame) -> None:
    DATABASE_DIR.mkdir(exist_ok=True)

    with duckdb.connect(DATABASE_PATH) as con:
        con.execute("""
            CREATE OR REPLACE TABLE raw_market_prices AS
            SELECT *
            FROM df
        """)

#Main Pipeline

def main():
    data = extract_market_data()
    df = transform_market_data(data)
    validate_market_data(df, expected_tickers)
    load_market_data(df)

if __name__ == "__main__":
    main()