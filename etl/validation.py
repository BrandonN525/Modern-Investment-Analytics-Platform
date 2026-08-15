import logging

#Logging Configuration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

#Market Validation

def validate_market_data(df, expected_tickers):
    try:
        if df['ticker'].isna().any():
            raise ValueError("Market data contains null tickers.")
        if df['date'].isna().any():
            raise ValueError("Market data contains null dates.")
        if df['close'].isna().any():
            raise ValueError("Market data contains null closing prices.")
        if df['adj_close'].isna().any():
            raise ValueError("Market data contains null adjusted closing prices.")
        if df['volume'].isna().any():
            raise ValueError("Market data contains null volume.")

        if df.duplicated(['date', 'ticker']).any():
            raise ValueError("Market data contains duplicate date/ticker combinations.")

        if (df['high'] < df['low']).any():
            raise ValueError("Market data contains high/low price violations.")
        if (df['high'] < df['open']).any():
            raise ValueError("Market data contains high/open price violations.")
        if (df['high'] < df['close']).any():
            raise ValueError("Market data contains high/close price violations.")
        if (df['open'] < df['low']).any():
            raise ValueError("Market data contains open/low price violations.")
        if (df['close'] < df['low']).any():
            raise ValueError("Market data contains close/low price violations.")

        expected_tickers = set(expected_tickers)
        actual_tickers = set(df['ticker'].unique())
        missing_tickers = expected_tickers - actual_tickers

        if missing_tickers:
            raise ValueError(f'Missing tickers: {missing_tickers}')

        if (df['volume'] < 0).any():
            raise ValueError("Market data contains negative volume.")
        if (df['open'] <= 0).any():
            raise ValueError("Market data contains invalid open prices.")
        if (df['low'] <= 0).any():
            raise ValueError("Market data contains invalid low prices.")
        if (df['adj_close'] <= 0).any():
            raise ValueError("Market data contains invalid adjusted closing prices.")

    except Exception:
        logger.exception("Market data validation failed")
        raise