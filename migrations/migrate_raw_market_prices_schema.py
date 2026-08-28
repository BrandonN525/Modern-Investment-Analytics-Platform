from pathlib import Path
import duckdb

#Project Paths

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / 'data'
DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "investment_analytics.duckdb"

with duckdb.connect(DATABASE_PATH) as con:

    old_row_count = con.sql("""
        SELECT COUNT(*)
        FROM raw_market_prices
    """).fetchone()[0]

    old_tickers = con.sql("""
        SELECT DISTINCT ticker
        FROM raw_market_prices
        ORDER BY ticker
    """).fetchall()

    con.execute("""
        CREATE TABLE raw_market_prices_tmp (
            date TIMESTAMP NOT NULL,
            ticker VARCHAR NOT NULL,
            open DOUBLE NOT NULL,
            high DOUBLE NOT NULL,
            low DOUBLE NOT NULL,
            close DOUBLE NOT NULL,
            adj_close DOUBLE NOT NULL,
            volume BIGINT NOT NULL,
            PRIMARY KEY (date, ticker)
        );

        INSERT INTO raw_market_prices_tmp (
            date,
            ticker,
            open,
            high,
            low,
            close,
            adj_close,
            volume
        )
        SELECT
            date,
            ticker,
            open,
            high,
            low,
            close,
            adj_close,
            volume
        FROM raw_market_prices;
    """)

    new_row_count = con.sql("""
        SELECT COUNT(*)
        FROM raw_market_prices_tmp
    """).fetchone()[0]

    new_tickers = con.sql("""
        SELECT DISTINCT ticker
        FROM raw_market_prices_tmp
        ORDER BY ticker
    """).fetchall()

    new_table_no_nulls = con.sql("""
        SELECT COUNT(*)
        FROM raw_market_prices_tmp
        WHERE date IS NULL
        OR ticker IS NULL
        OR open IS NULL
        OR high IS NULL
        OR low IS NULL
        OR close IS NULL
        OR adj_close IS NULL
        OR volume IS NULL;
    """).fetchone()[0]

    new_table_no_dupes = con.sql("""
        SELECT COUNT(*)
        FROM (
            SELECT date, ticker
            FROM raw_market_prices_tmp
            GROUP BY date, ticker
            HAVING COUNT(*) > 1
        )
    """).fetchone()[0]

    assert new_table_no_nulls == 0

    assert new_table_no_dupes == 0

    assert old_row_count == new_row_count

    assert old_tickers == new_tickers

    con.execute("""
        DROP TABLE raw_market_prices;

        ALTER TABLE raw_market_prices_tmp RENAME TO raw_market_prices;
    """)

    final_row_count = con.sql("""
        SELECT COUNT(*)
        FROM raw_market_prices
    """).fetchone()[0]

    assert final_row_count == old_row_count

    table_desc = con.execute("""
        DESCRIBE raw_market_prices;
    """).fetchall()

    print(table_desc)