"""Market data adapters and cached synthetic-demo loaders."""
import logging
from pathlib import Path
import pandas as pd
import streamlit as st
import yfinance as yf
from src.analytics import make_synthetic_ohlcv
from src.ingestion import load_upload, validate_ohlcv_frame

logging.getLogger("yfinance").setLevel(logging.CRITICAL)


@st.cache_data(ttl=3600, show_spinner=False)
def get_synthetic_stock_data():
    """Return deterministic fictional OHLCV data for offline demonstration."""
    frame = make_synthetic_ohlcv()
    return frame, {
        "shortName": "DEMO_COMPANY — synthetic data",
        "longName": "Fictional company generated for offline demonstration",
        "marketCap": None,
        "sector": "Synthetic demo",
        "industry": "Fictional OHLCV series",
        "data_source": "Generated locally by FinSight Nexus; not real market data",
        "is_sample": True,
        "quality_report": {
            "input_rows": len(frame),
            "valid_rows": len(frame),
            "invalid_rows_removed": 0,
            "duplicate_dates_removed": 0,
            "date_start": frame.index.min(),
            "date_end": frame.index.max(),
        },
    }


# Backwards-compatible alias for older local versions of the app.
def get_sample_stock_data():
    return get_synthetic_stock_data()


@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(ticker: str, period: str, interval: str):
    """Fetch one ticker from Yahoo Finance, returning a transparent failure reason."""
    ticker = str(ticker or "").strip().upper()
    if not ticker:
        return pd.DataFrame(), {"shortName": "Unknown ticker", "fetch_error": "Enter a ticker symbol."}
    try:
        stock = yf.Ticker(ticker)
        frame = stock.history(period=period, interval=interval, auto_adjust=False, timeout=12)
        if frame is None or frame.empty:
            return pd.DataFrame(), {
                "shortName": ticker, "data_source": "Yahoo Finance via yfinance", "is_sample": False,
                "fetch_error": "The provider returned no price rows. Check the symbol, network access, and provider availability/rate limits.",
            }
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = [col[0] for col in frame.columns]
        required = ["Open", "High", "Low", "Close"]
        missing = [col for col in required if col not in frame.columns]
        if missing:
            return pd.DataFrame(), {"shortName": ticker, "fetch_error": "Provider response is missing columns: " + ", ".join(missing)}
        if "Volume" not in frame:
            frame["Volume"] = 0
        frame.index = pd.to_datetime(frame.index, errors="coerce", utc=True).tz_convert(None)
        frame.index.name = "Date"
        frame, report, message = validate_ohlcv_frame(frame.reset_index(), ticker)
        if frame.empty:
            return frame, {"shortName": ticker, "fetch_error": "Retrieved data failed validation: " + message}
        # Keep metadata lookup off the critical path; it can trigger extra provider calls.
        return frame, {
            "shortName": ticker, "longName": ticker, "marketCap": None,
            "sector": "Not retrieved", "industry": "Not retrieved",
            "data_source": "Yahoo Finance via yfinance", "is_sample": False,
            "quality_report": report,
        }
    except Exception as exc:
        reason = str(exc).strip().replace("\n", " ")[:300]
        lower = reason.lower()
        if any(term in lower for term in ["429", "rate limit", "too many requests"]):
            user_message = "Yahoo Finance appears to be rate-limiting requests. Wait before retrying or use uploaded/synthetic demo data."
        elif any(term in lower for term in ["timeout", "timed out", "connection", "network"]):
            user_message = "Could not reach Yahoo Finance (network/timeout). Check your connection or use uploaded/synthetic demo data."
        else:
            user_message = f"Live data request failed ({reason or type(exc).__name__}). Check the ticker and provider availability."
        return pd.DataFrame(), {
            "shortName": ticker, "data_source": "Yahoo Finance via yfinance", "is_sample": False,
            "fetch_error": user_message, "technical_error": reason,
        }


@st.cache_data(ttl=300, show_spinner=False)
def get_multi_stock_data(tickers: tuple[str, ...], period: str, interval: str):
    """Fetch requested symbols via cached per-symbol requests; return closes and failures."""
    series = {}
    failures = {}
    for ticker in tickers:
        frame, info = get_stock_data(ticker, period, interval)
        if frame is not None and not frame.empty and "Close" in frame:
            series[ticker] = frame["Close"].rename(ticker)
        else:
            failures[ticker] = info.get("fetch_error", "No usable price data returned.")
    closes = pd.concat(series.values(), axis=1).sort_index() if series else pd.DataFrame()
    if not closes.empty:
        closes = closes.dropna(how="all").dropna(axis=1, how="all")
    return closes, failures


def load_uploaded_stock_data(uploaded_file):
    """Backward-compatible adapter for previous project API."""
    kind, frame, report, message = load_upload(uploaded_file)
    if kind == "single":
        return frame, {
            "shortName": Path(uploaded_file.name).stem,
            "longName": f"User-uploaded dataset: {uploaded_file.name}",
            "marketCap": None, "sector": "User-provided data", "industry": "Uploaded OHLCV dataset",
            "data_source": f"User upload: {uploaded_file.name}", "is_sample": False,
            "is_upload": True, "quality_report": report,
        }, message
    return pd.DataFrame(), {}, message
