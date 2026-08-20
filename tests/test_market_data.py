import pandas as pd
from datetime import date
import duckdb
from etl.market_data import get_market_data_start_dates
from etl.market_data import extract_market_data
from unittest.mock import patch
import pytest

def test_get_market_data_start_date_with_existing_data(tmp_path):
    db_path = tmp_path / "test.duckdb"

    etfs = ['SPY', 'QQQ', 'IWM', 'VTI', 'VXUS', 'VT', 'BND', 'FZROX', 'FZILX', 'FXNAX', 'FBIIX']
    
    df = pd.DataFrame({'date': ['2026-08-14', '2026-08-14', '2026-08-15', '2026-08-15'], 'ticker': ['SPY', 'QQQ', 'SPY', 'QQQ']})

    df['date'] = pd.to_datetime(df['date'])

    with duckdb.connect(db_path) as con:
        con.execute("""
            CREATE TABLE raw_market_prices AS
            SELECT * FROM df
        """)

    start_dates = get_market_data_start_dates(etfs, db_path, date(2020,1,1))

    assert start_dates['SPY'] == date(2026, 8, 14)

def test_get_market_data_start_date_without_table(tmp_path):
    db_path = tmp_path / "test.duckdb"

    with duckdb.connect(db_path) as con:
        pass

    start_date = get_market_data_start_dates(db_path)

    assert start_date == date(2020, 1, 1)

def test_get_market_data_start_date_with_empty_table(tmp_path):
    db_path = tmp_path / "test.duckdb"

    with duckdb.connect(db_path) as con:
        con.execute("""
            CREATE TABLE raw_market_prices (
                date DATE,
                ticker VARCHAR
            )
        """)

    start_date = get_market_data_start_dates(db_path)

    assert start_date == date(2020, 1, 1)

def test_extract_market_data():
    mock_data = pd.DataFrame({
        'test': [1, 2, 3]
    })

    with patch('etl.market_data.yf.download', return_value = mock_data) as mock_download:
        result = extract_market_data(
            date(2026, 8, 1),
            date(2026,8, 15)
        )

    pd.testing.assert_frame_equal(result, mock_data)

    mock_download.assert_called_once_with(
        ['SPY', 'QQQ', 'IWM', 'VTI', 'VXUS', 'VT', 'BND'],
        start=date(2026, 8, 1),
        end=date(2026, 8, 15),
        auto_adjust=False
    )

def test_extract_market_data_raises_error():
    with patch(
        'etl.market_data.yf.download',
        side_effect = Exception("Yahoo Finance Failed")
    ):
        with pytest.raises(Exception, match='Yahoo Finance Failed'):
            extract_market_data(
                date(2026, 8, 1),
                date(2026, 8, 15)
            )