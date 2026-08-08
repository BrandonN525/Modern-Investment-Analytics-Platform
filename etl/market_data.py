import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

etfs = ['SPY', 'QQQ', 'IWM', 'VTI', 'VXUS', 'BND']

#Import Data from YFinance

data = yf.download(etfs, start='2020-01-01', end='2026-01-01')

data_df = pd.DataFrame(data)

df_long = data_df.stack(level='Ticker', future_stack=True).reset_index()

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
assert (df_long['high'] >= df_long['low']).all()

expected_tickers = {'BND', 'IWM', 'QQQ', 'SPY', 'VTI', 'VXUS'}
actual_tickers = set(df_long['ticker'].unique())
missing_tickers = expected_tickers - actual_tickers
if missing_tickers:
    raise ValueError(f'Missing tickers: {missing_tickers}')

#Export Market Data

df_long.to_csv(DATA_DIR / "ETFs_Stack.csv", index=False)