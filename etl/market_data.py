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

etfs = ['SPY', 'QQQ', 'IWM', 'VTI', 'VXUS', 'VT', 'BND', 'FZROX', 'FZILX', 'FXNAX', 'FBIIX']

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(__name__)

HISTORICAL_START_DATE = date(2020, 1, 1)

#Source Start Dates

def get_source_start_dates(tickers, historical_start_date=HISTORICAL_START_DATE):
    source_start_dates = {}

    for ticker in tickers:
        try:
            data = yf.download(ticker, start=historical_start_date, end=date.today(), auto_adjust=False)

            if data.empty:
                source_start_dates[ticker] = None
                continue

            data = data.stack(level='Ticker', future_stack=True).reset_index()
            
            data = data.dropna(subset=['Date', 'Ticker', 'Close', 'Adj Close', 'High', 'Low', 'Open', 'Volume'])

            source_start_dates[ticker] = data['Date'].min()

        except Exception:
            logger.exception("Failed to determine source start date for %s", ticker)
            raise

    return source_start_dates

#Metadata Check

def get_market_data_start_dates(tickers, database_path=DATABASE_PATH, historical_start_date = HISTORICAL_START_DATE) -> dict:
    try:

        source_start_dates = get_source_start_dates(tickers, historical_start_date)

        with duckdb.connect(database_path) as con:
            table_exists = con.sql("""
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'main'
                AND table_name = 'raw_market_prices'
            """).fetchone()

            if table_exists is None:
                return {ticker: historical_start_date for ticker in tickers}

            metadata = con.sql("""
                SELECT ticker, MIN(date) as min_date, MAX(date) as max_date
                FROM raw_market_prices
                GROUP BY ticker""").fetchall()

            ticker_metadata = {ticker: {'min_date': min_date, 'max_date': max_date} for ticker, min_date, max_date in metadata}

            start_dates = {}

            for ticker in tickers:
                if ticker not in ticker_metadata:
                    start_dates[ticker] = historical_start_date
                    continue

                db_min_date = ticker_metadata[ticker]['min_date']
                db_max_date = ticker_metadata[ticker]['max_date']

                source_min_date = source_start_dates[ticker]

                if source_min_date is None:
                    start_dates[ticker] = db_max_date.date()
                    continue

                if db_min_date.date() > source_min_date.date():
                    start_dates[ticker] = historical_start_date

                else:
                    start_dates[ticker] = db_max_date.date()

        return start_dates
    
    except Exception:
        logger.exception("Metadata check failed")
        raise

#Extract - Download market data from Yahoo Finance

def extract_market_data(tickers, start_date: date, end_date: date) -> pd.DataFrame:
    logger.info("Extracting market data for %d ETFs from %s to %s", len(tickers), start_date, end_date)

    try:
        data = yf.download(tickers, start=start_date, end=end_date, auto_adjust=False)
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

        null_count = df_long[['date', 'ticker', 'close', 'adj_close', 'high', 'low', 'open', 'volume']].isnull().any(axis=1).sum()

        if null_count > 0:
            logger.info("%d rows with missing values detected", null_count)
            df_long = df_long.dropna(subset=['date', 'ticker', 'close', 'adj_close', 'high', 'low', 'open', 'volume'])
            logger.info("%d rows with missing values removed", null_count)

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

def load_market_data(df: pd.DataFrame, database_path=DATABASE_PATH) -> None:
    logger.info("Loading market data into DuckDB")
    DATABASE_DIR.mkdir(exist_ok=True)

    try:
        with duckdb.connect(database_path) as con:
            table_exists = con.sql("""
                           SELECT 1
                           FROM information_schema.tables
                           WHERE table_schema = 'main'
                           AND table_name = 'raw_market_prices'""").fetchone()
            
            if table_exists is None:
                con.execute("""
                    CREATE TABLE raw_market_prices AS
                    SELECT *
                    FROM df
                """)
                
                row_count = con.sql("""
                    SELECT COUNT(*)
                    FROM raw_market_prices
                """).fetchone()[0]

                logger.info("Created raw_market_prices with %d rows", row_count)

            else:
                logger.info("Existing table detected")

                row_count = con.sql("""
                    SELECT COUNT(*)
                    FROM df
                """).fetchone()[0]

                logger.info("Extracted %d rows", row_count)

                new_row_count = con.sql("""
                    SELECT COUNT(*)
                    FROM df
                    WHERE NOT EXISTS(
                        SELECT 1
                        FROM raw_market_prices existing
                        WHERE existing.date = df.date
                        AND existing.ticker = df.ticker
                    )
                """).fetchone()[0]
                
                logger.info("%d new rows identified for insertion", new_row_count)

                con.execute("""
                    INSERT INTO raw_market_prices
                    SELECT *
                    FROM df
                    WHERE NOT EXISTS(
                        SELECT 1
                        FROM raw_market_prices existing
                        WHERE existing.date = df.date
                        AND existing.ticker = df.ticker
                    )
                """)

                logger.info("Inserted %d new rows", new_row_count)

            logger.info("Market data load complete")

    except Exception:
        logger.exception("Market data loading failed")
        raise

#Main Pipeline

def main():
    logger.info("Starting market data pipeline")

    start_dates = get_market_data_start_dates(etfs)
    end_date = date.today()

    extraction_groups = {}

    for ticker, start_date in start_dates.items():
        extraction_groups.setdefault(start_date, [])
        extraction_groups[start_date].append(ticker)

    logger.info("Utilizing the following tickers grouped by start date: %s", extraction_groups)

    try:
        for start_date, tickers in extraction_groups.items():
            logger.info("Processing %d tickers from %s to %s: %s", len(tickers), start_date, end_date, tickers)

            #To do: extract data for this group

            data = extract_market_data(tickers, start_date, end_date)

            #To do: Transform extracted data

            df = transform_market_data(data)

            #To do: Validate against the tickers in this group
            
            logger.info("Validating market data")
            validate_market_data(df, set(tickers))
            logger.info("Market data validation passed")

            #To do: Load the transformed data 

            load_market_data(df)

    except Exception:
        logger.exception("Market data pipeline failed")
        raise

    logger.info("Market data pipeline completed successfully")

if __name__ == "__main__":
    main()