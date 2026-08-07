import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

etfs = ['SPY', 'QQQ', 'IWM', 'VTI', 'VXUS', 'BND']

data = yf.download(etfs, start='2020-01-01', end='2026-01-01')

data_df = pd.DataFrame(data)

df_long = data_df.stack(level="Ticker", future_stack=True).reset_index()
