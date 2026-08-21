import pandas as pd
from datetime import date
import duckdb
from etl.market_data import (
    get_source_start_dates,
    get_market_data_start_dates,
    extract_market_data
)
from unittest.mock import patch
import pytest

def test_get_source_start_dates():

    dates = pd.to_datetime(['2020-01-02', '2020-01-03', '2020-01-06'])

    dates.name = 'Date'

    columns = pd.MultiIndex.from_product(
        [
            ['Close', 'Adj Close', 'High', 'Low', 'Open', 'Volume'],
            ['SPY']
        ],
        names=['Price', 'Ticker']
    )

    data = pd.DataFrame(
        [
            [100, 100, 101, 99, 100, 1000],
            [101, 101, 102, 100, 101, 1100],
            [102, 102, 103, 101, 102, 1200]
        ],
        index=dates,
        columns=columns
    )

    with patch('etl.market_data.yf.download', return_value = data):
        result = get_source_start_dates(['SPY'], date(2020, 1, 1))

    assert result['SPY'] == pd.Timestamp('2020-01-02')

def test_get_source_start_dates_with_empty_data():

    with patch('etl.market_data.yf.download', return_value = pd.DataFrame()):
        result = get_source_start_dates(['SPY'], date(2020, 1, 1))

    assert result['SPY'] is None


def test_get_market_data_start_dates_existing_ticker_incomplete_history(tmp_path):

    db_path = tmp_path / "test.duckdb"

    tickers = ['SPY']
    
    df = pd.DataFrame({'date': ['2026-08-14', '2026-08-15'], 'ticker': ['SPY', 'SPY']})

    df['date'] = pd.to_datetime(df['date'])

    with duckdb.connect(db_path) as con:
        con.execute("""
            CREATE TABLE raw_market_prices AS
            SELECT * FROM df
        """)

    with patch('etl.market_data.get_source_start_dates', return_value = {'SPY': pd.Timestamp('2020-01-02')}):
        start_dates = get_market_data_start_dates(tickers, db_path, date(2020,1,1))

    assert start_dates['SPY'] == date(2020, 1, 1)

def test_get_market_data_start_dates_existing_ticker_complete_history(tmp_path):

    db_path = tmp_path / "test.duckdb"

    tickers = ['SPY']
    
    df = pd.DataFrame({'date': ['2020-01-02', '2026-08-18'], 'ticker': ['SPY', 'SPY']})

    df['date'] = pd.to_datetime(df['date'])

    with duckdb.connect(db_path) as con:
        con.execute("""
            CREATE TABLE raw_market_prices AS
            SELECT * FROM df
        """)

    with patch('etl.market_data.get_source_start_dates', return_value = {'SPY': pd.Timestamp('2020-01-02')}):
        start_dates = get_market_data_start_dates(tickers, db_path, date(2020, 1, 1))

    assert start_dates['SPY'] == date(2026, 8, 18)

def test_get_market_data_start_dates_without_table(tmp_path):

    db_path = tmp_path / "test.duckdb"

    tickers = ['SPY', 'QQQ']

    with duckdb.connect(db_path) as con:
        pass

    with patch('etl.market_data.get_source_start_dates', return_value = {'SPY': pd.Timestamp('2020-01-02'), 'QQQ': pd.Timestamp('2020-01-02')}):
        start_dates = get_market_data_start_dates(tickers, db_path, date(2020, 1, 1))

    assert start_dates == {'SPY': date(2020, 1, 1), 'QQQ': date(2020, 1, 1)}

def test_get_market_data_start_dates_new_ticker(tmp_path):

    db_path = tmp_path / "test.duckdb"

    tickers = ['SPY', 'VT']

    df = pd.DataFrame({'date': ['2020-01-02', '2026-08-18'], 'ticker': ['SPY', 'SPY']})

    df['date'] = pd.to_datetime(df['date'])

    with duckdb.connect(db_path) as con:
        con.execute("""
            CREATE TABLE raw_market_prices AS
            SELECT * FROM df
        """)

    with patch('etl.market_data.get_source_start_dates', return_value = {'SPY': pd.Timestamp('2026-08-18'), 'VT': pd.Timestamp('2008-01-01')}):
        start_dates = get_market_data_start_dates(tickers, db_path, date(2020, 1, 1))

    assert start_dates['SPY'] == date(2026, 8, 18)
    assert start_dates['VT'] == date(2020, 1, 1)

def test_get_market_data_start_date_with_empty_table(tmp_path):

    db_path = tmp_path / "test.duckdb"

    tickers = ['SPY', 'QQQ']

    with duckdb.connect(db_path) as con:
        con.execute("""
            CREATE TABLE raw_market_prices (
                date DATE,
                ticker VARCHAR
            )
        """)

    with patch('etl.market_data.get_source_start_dates', return_value = {'SPY': pd.Timestamp('2020-01-02'), 'QQQ': pd.Timestamp('2020-01-02')}):
        start_dates = get_market_data_start_dates(tickers, db_path, date(2020, 1, 1))

    assert start_dates == {'SPY': date(2020, 1, 1), 'QQQ': date(2020, 1, 1)}

def test_extract_market_data():

    mock_data = pd.DataFrame({
        'test': [1, 2, 3]
    })

    tickers = ['SPY', 'QQQ']

    with patch('etl.market_data.yf.download', return_value = mock_data) as mock_download:
        result = extract_market_data(
            tickers,
            date(2026, 8, 1),
            date(2026,8, 15)
        )

    pd.testing.assert_frame_equal(result, mock_data)

    mock_download.assert_called_once_with(
        tickers,
        start=date(2026, 8, 1),
        end=date(2026, 8, 15),
        auto_adjust=False
    )

def test_get_source_start_dates_raises_error():

    with patch('etl.market_data.yf.download', side_effect = Exception("Yahoo Finance Failed")
    ):
        with pytest.raises(Exception, match='Yahoo Finance Failed'):
            get_source_start_dates(['SPY'], date(2020, 1, 1))

def test_extract_market_data_raises_error():

    with patch('etl.market_data.yf.download', side_effect = Exception("Yahoo Finance Failed")
        ):
            with pytest.raises(Exception, match='Yahoo Finance Failed'):
                extract_market_data(['SPY', 'QQQ'], date(2026, 8, 1), date(2026, 8, 15))