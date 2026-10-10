import pandas as pd


def format_number(value):
    try:
        if value is None or pd.isna(value):
            return "N/A"
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate moving averages, RSI and MACD without mutating the input frame."""
    if df is None or df.empty or "Close" not in df.columns:
        return df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    frame = df.copy().sort_index()
    close = pd.to_numeric(frame["Close"], errors="coerce")
    frame["MA50"] = close.rolling(window=50, min_periods=50).mean()
    frame["MA200"] = close.rolling(window=200, min_periods=200).mean()
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    frame["RSI14"] = 100 - (100 / (1 + rs))
    frame.loc[(avg_loss == 0) & (avg_gain > 0), "RSI14"] = 100
    frame.loc[(avg_loss == 0) & (avg_gain == 0), "RSI14"] = 50
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    frame["MACD"] = ema12 - ema26
    frame["MACD_Signal"] = frame["MACD"].ewm(span=9, adjust=False).mean()
    frame["MACD_Histogram"] = frame["MACD"] - frame["MACD_Signal"]
    return frame
