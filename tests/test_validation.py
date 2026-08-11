import pandas as pd
import pytest
from etl.validation import validate_market_data

def create_valid_market_data() -> pd.DataFrame:
    valid_df = pd.DataFrame([
        {'date': '2026-01-01', 'ticker': 'SPY', 'open': 100, 'high': 105, 'low': 95, 'close': 103, 'adj_close': 103, 'volume': 100000},
        {'date': '2026-01-01', 'ticker': 'QQQ', 'open': 200, 'high': 210, 'low': 195, 'close': 205, 'adj_close': 205, 'volume': 200000}
    ])

    valid_df['date'] = pd.to_datetime(valid_df['date'])
    return valid_df

def test_valid_market_data():
    df = create_valid_market_data()
    expected_tickers = {'SPY', 'QQQ'}

    validate_market_data(df, expected_tickers)

def test_null_ticker_raises_error():
    df = create_valid_market_data()
    df.loc[0, 'ticker'] = None

    with pytest.raises(ValueError, match='null tickers'):
        validate_market_data(df, {'SPY', 'QQQ'})

def test_null_date_raises_error():
    df = create_valid_market_data()
    df.loc[0, 'date'] = None

    with pytest.raises(ValueError, match='null dates'):
        validate_market_data(df, {'SPY', 'QQQ'})

def test_null_close_raises_error():
    df = create_valid_market_data()
    df.loc[0, 'close'] = None

    with pytest.raises(ValueError, match='null closing prices'):
        validate_market_data(df, {'SPY', 'QQQ'})

def test_null_adj_close_raises_error():
    df = create_valid_market_data()
    df.loc[0, 'adj_close'] = None

    with pytest.raises(ValueError, match='null adjusted closing prices'):
        validate_market_data(df, {'SPY', 'QQQ'})

def test_null_volume_raises_error():
    df = create_valid_market_data()
    df.loc[0, 'volume'] = None

    with pytest.raises(ValueError, match='null volume'):
        validate_market_data(df, {'SPY', 'QQQ'})