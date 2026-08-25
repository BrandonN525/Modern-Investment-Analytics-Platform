import pandas as pd
from datetime import date, datetime
import duckdb
from etl.market_data import (
    get_source_start_dates,
    get_market_data_start_dates,
    extract_market_data,
    transform_market_data,
    load_market_data,
    HISTORICAL_START_DATE,
    main
)
from unittest.mock import patch, call
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

def test_get_market_data_start_dates_handles_multiple_tickers(tmp_path):

    db_path = tmp_path / "test.duckdb"

    tickers = ['SPY', 'QQQ', 'FZROX']

    source_start_dates = {
        'SPY': pd.Timestamp('2020-01-02'),
        'QQQ': pd.Timestamp('2020-01-02'),
        'FZROX': pd.Timestamp('2021-01-04')
    }

    with duckdb.connect(db_path) as con:

        con.execute("""
            CREATE TABLE raw_market_prices (
                date TIMESTAMP_NS,
                ticker VARCHAR,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                adj_close DOUBLE,
                volume BIGINT
            )
        """)

        con.execute("""
            INSERT INTO raw_market_prices VALUES
                ('2020-01-02', 'SPY', 1, 1, 1, 1, 1, 1),
                ('2026-08-18', 'SPY', 1, 1, 1, 1, 1, 1),
                ('2022-01-03', 'QQQ', 1, 1, 1, 1, 1, 1),
                ('2026-08-18', 'QQQ', 1, 1, 1, 1, 1, 1)
        """)    

    with patch(
        'etl.market_data.get_source_start_dates',
        return_value = source_start_dates
    ):

        result = get_market_data_start_dates(tickers, db_path, HISTORICAL_START_DATE)

        assert result == {
            'SPY': date(2026, 8, 18),
            'QQQ': HISTORICAL_START_DATE,
            'FZROX': HISTORICAL_START_DATE
        }

def test_get_market_data_start_dates_uses_db_max_when_no_source_data(tmp_path):

    db_path = tmp_path / "duck.db"

    tickers = ['SPY']

    source_start_dates = {
        'SPY': None
    }

    with duckdb.connect(db_path) as con:
    
        con.execute("""
            CREATE TABLE raw_market_prices (
                date TIMESTAMP_NS,
                ticker VARCHAR,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                adj_close DOUBLE,
                volume BIGINT
            )
        """)
    
        con.execute("""
            INSERT INTO raw_market_prices VALUES
                ('2020-01-02', 'SPY', 1, 1, 1, 1, 1, 1),
                ('2026-08-18', 'SPY', 1, 1, 1, 1, 1, 1)
        """)    
    
    with patch(
        'etl.market_data.get_source_start_dates',
        return_value = source_start_dates
    ):
    
        result = get_market_data_start_dates(tickers, db_path, HISTORICAL_START_DATE)
    
        assert result == {
            'SPY': date(2026, 8, 18)
        }

def test_get_market_data_start_dates_handles_missing_table(tmp_path):

    db_path = tmp_path / "duck.db"

    tickers = ['SPY', 'QQQ', 'FZROX']

    source_start_dates = {
        'SPY': pd.Timestamp('2020-01-02'),
        'QQQ': pd.Timestamp('2020-01-02'),
        'FZROX': pd.Timestamp('2021-01-04')
    }
    
    with patch(
        'etl.market_data.get_source_start_dates',
        return_value = source_start_dates
    ):
    
        result = get_market_data_start_dates(tickers, db_path, HISTORICAL_START_DATE)
    
        assert result == {
            'SPY': HISTORICAL_START_DATE,
            'QQQ': HISTORICAL_START_DATE,
            'FZROX': HISTORICAL_START_DATE
        }

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

def test_transform_market_data():
    
    dates = pd.to_datetime(['2020-01-02', '2020-01-03'])
    
    dates.name = 'Date'
    
    columns = pd.MultiIndex.from_product(
        [
            ['Close', 'Adj Close', 'High', 'Low', 'Open', 'Volume'],
            ['QQQ', 'SPY']
        ],
        names=['Price', 'Ticker']
    )
    
    data = pd.DataFrame(
        [
            [100.02, 200.02, 100.2210021, 200.2210021, 105.902179, 205.902179, 99.8102780, 199.8102780, 100.414, 200.414, 1000, 2000],
            [101.123456789, 201.123456789, 101.4719208, 201.4719208, 102.374819, 202.374819, 100.38390, 200.38390, 101.917, 201.917, 1100, 2100]
        ],
        index=dates,
        columns=columns
    )

    result = transform_market_data(data)

    expected = pd.DataFrame([
        {'date': pd.to_datetime('2020-01-02'), 'ticker': 'QQQ', 'close': 100.02, 'adj_close': 100.221002, 'high': 105.902179, 'low': 99.810278, 'open': 100.414, 'volume': 1000},
        {'date': pd.to_datetime('2020-01-02'), 'ticker': 'SPY', 'close': 200.02, 'adj_close': 200.221002, 'high': 205.902179, 'low': 199.810278, 'open': 200.414, 'volume': 2000},
        {'date': pd.to_datetime('2020-01-03'), 'ticker': 'QQQ', 'close': 101.123457, 'adj_close': 101.471921, 'high': 102.374819, 'low': 100.38390, 'open': 101.917, 'volume': 1100},
        {'date': pd.to_datetime('2020-01-03'), 'ticker': 'SPY', 'close': 201.123457, 'adj_close': 201.471921, 'high': 202.374819, 'low': 200.38390, 'open': 201.917, 'volume': 2100}
    ])

    expected.columns.name = 'Price'
    expected['ticker'] = expected['ticker'].astype('string')
    expected['volume'] = expected['volume'].astype('Int64')

    pd.testing.assert_frame_equal(result, expected)

def test_transform_market_data_removes_null_rows():
    
    dates = pd.to_datetime(['2020-01-02', '2020-01-03'])
    
    dates.name = 'Date'
    
    columns = pd.MultiIndex.from_product(
        [
            ['Close', 'Adj Close', 'High', 'Low', 'Open', 'Volume'],
            ['QQQ', 'SPY']
        ],
        names=['Price', 'Ticker']
    )
    
    data = pd.DataFrame(
        [
            [100.02, None, 100.2210021, 200.2210021, 105.902179, 205.902179, 99.8102780, 199.8102780, 100.414, 200.414, 1000, 2000],
            [101.123456789, 201.123456789, 101.4719208, 201.4719208, 102.374819, 202.374819, 100.38390, 200.38390, 101.917, 201.917, 1100, 2100]
        ],
        index=dates,
        columns=columns
    )

    result = transform_market_data(data)

    expected = pd.DataFrame([
        {'date': pd.to_datetime('2020-01-02'), 'ticker': 'QQQ', 'close': 100.02, 'adj_close': 100.221002, 'high': 105.902179, 'low': 99.810278, 'open': 100.414, 'volume': 1000},
        {'date': pd.to_datetime('2020-01-03'), 'ticker': 'QQQ', 'close': 101.123457, 'adj_close': 101.471921, 'high': 102.374819, 'low': 100.38390, 'open': 101.917, 'volume': 1100},
        {'date': pd.to_datetime('2020-01-03'), 'ticker': 'SPY', 'close': 201.123457, 'adj_close': 201.471921, 'high': 202.374819, 'low': 200.38390, 'open': 201.917, 'volume': 2100}
    ])

    expected.columns.name = 'Price'
    expected['ticker'] = expected['ticker'].astype('string')
    expected['volume'] = expected['volume'].astype('Int64')

    result = result.reset_index(drop=True)

    expected = expected.reset_index(drop=True)

    pd.testing.assert_frame_equal(result, expected)

def test_load_market_data(tmp_path):

    db_path = tmp_path / "test.duckdb"

    df = pd.DataFrame([
        {
            'date': pd.to_datetime('2026-08-18'),
            'ticker': 'SPY',
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'adj_close': 103.0,
            'volume': 100000
        },
        {
            'date': pd.to_datetime('2026-08-18'),
            'ticker': 'QQQ',
            'open': 200.0,
            'high': 205.0,
            'low': 199.0,
            'close': 203.0,
            'adj_close': 203.0,
            'volume': 200000
        }
    ])

    load_market_data(df, db_path)

    with duckdb.connect(db_path) as con:

        table_exists = con.sql("""
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'main'
            AND table_name = 'raw_market_prices'
        """).fetchone()

        assert table_exists is not None

        row_count = con.sql("""
            SELECT COUNT(*)
            FROM raw_market_prices
        """).fetchone()[0]

        assert row_count == 2

        rows = con.sql("""
            SELECT date, ticker, close
            FROM raw_market_prices
            ORDER BY ticker
        """).fetchall()

        assert rows == [
            (datetime(2026, 8, 18), 'QQQ', 203.0),
            (datetime(2026, 8, 18), 'SPY', 103.0)
        ]

def test_load_market_data_handles_duplicate_rows(tmp_path):

    db_path = tmp_path / "duck.db"

    df = pd.DataFrame([
        {
            'date': pd.to_datetime('2026-08-18'),
            'ticker': 'SPY',
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'adj_close': 103.0,
            'volume': 100000
        },
        {
            'date': pd.to_datetime('2026-08-19'),
            'ticker': 'SPY',
            'open': 200.0,
            'high': 205.0,
            'low': 199.0,
            'close': 203.0,
            'adj_close': 203.0,
            'volume': 200000
        }
    ])

    with duckdb.connect(db_path) as con:
    
        con.execute("""
            CREATE TABLE raw_market_prices (
                date TIMESTAMP_NS,
                ticker VARCHAR,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                adj_close DOUBLE,
                volume BIGINT
            )
        """)
    
        con.execute("""
            INSERT INTO raw_market_prices VALUES
                ('2020-01-02', 'SPY', 1, 1, 1, 1, 1, 1),
                ('2026-08-18', 'SPY', 100.0, 105.0, 99.0, 103.0, 103.0, 100000)
        """)

    load_market_data(df, db_path)
    
    with duckdb.connect(db_path) as con:

        spy_dates = con.sql("""
                        SELECT date
                        FROM raw_market_prices
                        WHERE ticker = 'SPY'
                        ORDER BY date
                    """).fetchall()

        assert spy_dates == [
            (datetime(2020, 1, 2),),
            (datetime(2026, 8, 18),),
            (datetime(2026, 8, 19),)
        ]

def test_load_market_data_handles_new_ticker(tmp_path):
    db_path = tmp_path / "duck.db"
    
    df = pd.DataFrame([
        {
            'date': pd.to_datetime('2026-08-18'),
            'ticker': 'QQQ',
            'open': 200.0,
            'high': 205.0,
            'low': 199.0,
            'close': 203.0,
            'adj_close': 203.0,
            'volume': 200000
        },
        {
            'date': pd.to_datetime('2026-08-19'),
            'ticker': 'QQQ',
            'open': 300.0,
            'high': 305.0,
            'low': 299.0,
            'close': 303.0,
            'adj_close': 303.0,
            'volume': 300000
        }
    ])

    with duckdb.connect(db_path) as con:
    
        con.execute("""
            CREATE TABLE raw_market_prices (
                date TIMESTAMP_NS,
                ticker VARCHAR,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                adj_close DOUBLE,
                volume BIGINT
            )
        """)
    
        con.execute("""
            INSERT INTO raw_market_prices VALUES
                ('2020-01-02', 'SPY', 1, 1, 1, 1, 1, 1),
                ('2026-08-18', 'SPY', 100.0, 105.0, 99.0, 103.0, 103.0, 100000)
        """)

    load_market_data(df, db_path)
    
    with duckdb.connect(db_path) as con:

        qqq_rows = con.sql("""
                        SELECT date, ticker, close
                        FROM raw_market_prices
                        WHERE ticker = 'QQQ'
                        ORDER BY date
                    """).fetchall()

        assert qqq_rows == [
            (datetime(2026, 8, 18), 'QQQ', 203.0),
            (datetime(2026, 8, 19), 'QQQ', 303.0)
        ]

def test_load_market_data_preserves_existing_rows(tmp_path):
    db_path = tmp_path / "duck.db"
    
    df = pd.DataFrame([
        {
            'date': pd.to_datetime('2026-08-18'),
            'ticker': 'SPY',
            'open': 200.0,
            'high': 205.0,
            'low': 199.0,
            'close': 203.0,
            'adj_close': 203.0,
            'volume': 200000
        }
    ])

    with duckdb.connect(db_path) as con:
    
        con.execute("""
            CREATE TABLE raw_market_prices (
                date TIMESTAMP_NS,
                ticker VARCHAR,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                adj_close DOUBLE,
                volume BIGINT
            )
        """)
    
        con.execute("""
            INSERT INTO raw_market_prices VALUES
                ('2026-08-18', 'SPY', 100.0, 105.0, 99.0, 103.0, 103.0, 100000)
        """)

    load_market_data(df, db_path)
    
    with duckdb.connect(db_path) as con:

        spy_row = con.sql("""
                        SELECT date, ticker, open, high, low, close, adj_close, volume
                        FROM raw_market_prices
                        WHERE ticker = 'SPY'
                    """).fetchall()

        assert spy_row == [
            (datetime(2026, 8, 18), 'SPY', 100.0, 105.0, 99.0, 103.0, 103.0, 100000)
        ]

def test_main_groups_tickers_by_start_date():

    with patch(
        'etl.market_data.get_market_data_start_dates',
        return_value = {
            'SPY': date(2026, 8, 18),
            'QQQ': date(2020, 1, 1),
            'FZROX': date(2026, 8, 18)
        }
    ), patch(
        'etl.market_data.extract_market_data',
        return_value = pd.DataFrame()
    ) as mock_extract, patch(
        'etl.market_data.transform_market_data',
        return_value = pd.DataFrame()
    ), patch(
        'etl.market_data.validate_market_data'
    ), patch(
        'etl.market_data.load_market_data'
    ):
        main()

        assert mock_extract.call_count == 2

        assert call(
            ['SPY', 'FZROX'],
            date(2026, 8, 18),
            date.today()
        ) in mock_extract.call_args_list

        assert call(
            ['QQQ'],
            date(2020, 1, 1),
            date.today()
        ) in mock_extract.call_args_list

def test_main_runs_validation_and_load_for_each_group():

    transformed_df = pd.DataFrame([
        {
            'date': pd.to_datetime('2026-08-18'),
            'ticker': 'SPY',
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'adj_close': 103.0,
            'volume': 100000
        },
        {
            'date': pd.to_datetime('2026-08-18'),
            'ticker': 'QQQ',
            'open': 200.0,
            'high': 205.0,
            'low': 199.0,
            'close': 203.0,
            'adj_close': 203.0,
            'volume': 200000
        }
    ])

    with patch(
        'etl.market_data.get_market_data_start_dates',
        return_value = {
            'SPY': date(2026, 8, 18),
            'QQQ': date(2020, 1, 1)
        }
    ), patch(
        'etl.market_data.extract_market_data',
        return_value = pd.DataFrame()
    ) as mock_extract, patch(
        'etl.market_data.transform_market_data',
        return_value = transformed_df
    ) as mock_transform, patch(
        'etl.market_data.validate_market_data'
    ) as mock_validate, patch(
        'etl.market_data.load_market_data'
    ) as mock_load:

        main()

        assert mock_extract.call_count == 2

        assert call(
            ['SPY'],
            date(2026, 8, 18),
            date.today()
        ) in mock_extract.call_args_list

        assert call(
            ['QQQ'],
            date(2020, 1, 1),
            date.today()
        ) in mock_extract.call_args_list

        assert mock_transform.call_count == 2

        assert mock_validate.call_count == 2

        assert mock_load.call_count == 2

        assert mock_validate.call_args_list[0].args[0] is transformed_df

        assert mock_validate.call_args_list[1].args[0] is transformed_df

        assert set(mock_validate.call_args_list[0].args[1]) == {'SPY'}

        assert set(mock_validate.call_args_list[1].args[1]) == {'QQQ'}

        assert mock_load.call_args_list[0].args[0] is transformed_df
        
        assert mock_load.call_args_list[1].args[0] is transformed_df