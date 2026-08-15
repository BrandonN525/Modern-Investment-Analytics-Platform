import yfinance as yf
import pandas as pd
from pathlib import Path
import duckdb
from etl.validation import validate_market_data
import logging
from datetime import date

#Project Paths

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / 'data'
DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "investment_analytics.duckdb"

#Configuration

etfs = ['SPY', 'QQQ', 'IWM', 'VTI', 'VXUS', 'VT', 'BND']
expected_tickers = {'BND', 'IWM', 'QQQ', 'SPY', 'VTI', 'VXUS', 'VT'}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(__name__)

#Extract - Download market data from Yahoo Finance

def extract_market_data(start_date: date, end_date: date) -> pd.DataFrame:
    logger.info("Extracting market data for %d ETFs from %s to %s", len(etfs), start_date, end_date)

    try:
        data = yf.download(etfs, start=start_date, end=end_date, auto_adjust=False)
    except Exception:
        logger.exception("Market data extraction failed")
        raise

    logger.info("Market data extraction complete")

    return data

#Transform - Normalize and standardize market data

def transform_market_data(data: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transforming market data")

    try:
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
    except Exception:
        logger.exception("Market data transformation failed")
        raise

    logger.info("Market data transformation complete: %d rows across %d tickers", len(df_long), df_long['ticker'].nunique())

    return df_long

#Load - Write validated data to DuckDB

def load_market_data(df: pd.DataFrame) -> None:
    logger.info("Loading market data into DuckDB")
    DATABASE_DIR.mkdir(exist_ok=True)

    try:
        with duckdb.connect(DATABASE_PATH) as con:
            con.execute("""
                CREATE OR REPLACE TABLE raw_market_prices AS
                SELECT *
                FROM df
            """)

            row_count = con.sql("""SELECT COUNT(*) FROM raw_market_prices""").fetchone()[0]
            logger.info("Successfully loaded %d rows", row_count)
    except Exception:
        logger.exception("Market data loading failed")
        raise

#Main Pipeline

def main():
    logger.info("Starting market data pipeline")

    start_date = date(2020, 1, 1)
    end_date = date.today()

    try:
        data = extract_market_data(start_date, end_date)
        df = transform_market_data(data)

        logger.info("Validating market data")
        validate_market_data(df, expected_tickers)
        logger.info("Market data validation passed")

        load_market_data(df)

    except Exception:
        logger.exception("Market data pipeline failed")
        raise

    logger.info("Market data pipeline completed successfully")

if __name__ == "__main__":
    main()