"""Validated CSV/Excel ingestion for single-company and multi-company data."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import io
import numpy as np
import pandas as pd

OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]
_REQUIRED_OHLC = ["Date", "Open", "High", "Low", "Close"]
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def _read_upload(uploaded_file: Any) -> pd.DataFrame:
    name = getattr(uploaded_file, "name", "uploaded.csv")
    suffix = Path(name).suffix.lower()
    content = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds the 20 MB upload limit. Split the file into smaller parts and try again.")
    if suffix == ".csv":
        return pd.read_csv(io.BytesIO(content))
    if suffix == ".xlsx":
        return pd.read_excel(io.BytesIO(content), engine="openpyxl")
    if suffix == ".xls":
        return pd.read_excel(io.BytesIO(content), engine="xlrd")
    raise ValueError("Unsupported file type. Upload a .csv, .xlsx, or .xls file.")


def _normalise_headers(frame: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "date": "Date", "datetime": "Date", "timestamp": "Date", "time": "Date",
        "ticker": "Ticker", "symbol": "Ticker", "company": "Ticker", "company ticker": "Ticker",
        "open": "Open", "high": "High", "low": "Low", "close": "Close",
        "adj close": "Adj Close", "adjusted close": "Adj Close", "adjustedclose": "Adj Close",
        "volume": "Volume", "vol": "Volume",
    }
    rename = {}
    canonical_seen: dict[str, str] = {}
    for col in frame.columns:
        key = " ".join(str(col).strip().lower().replace("_", " ").replace("-", " ").split())
        canonical = aliases.get(key, str(col).strip())
        if canonical in canonical_seen:
            raise ValueError(f"Duplicate columns after header normalization: '{canonical_seen[canonical]}' and '{col}' both map to '{canonical}'. Keep only one of them.")
        canonical_seen[canonical] = str(col)
        rename[col] = canonical
    return frame.rename(columns=rename)


def _quality_score(input_rows: int, valid_rows: int, anomalies: int = 0) -> float:
    if input_rows <= 0:
        return 0.0
    row_score = 100 * valid_rows / input_rows
    anomaly_penalty = min(20.0, 20 * anomalies / max(input_rows, 1))
    return round(max(0.0, row_score - anomaly_penalty), 1)


def validate_ohlcv_frame(raw: pd.DataFrame, source_name: str = "uploaded data") -> tuple[pd.DataFrame, dict, str]:
    """Validate single-company OHLCV. Invalid OHLC rows are removed; volume anomalies are reported."""
    if raw is None or raw.empty:
        return pd.DataFrame(), {"input_rows": 0, "valid_rows": 0, "quality_score": 0.0}, "The uploaded file contains no rows."
    try:
        raw = _normalise_headers(raw.copy())
    except ValueError as exc:
        return pd.DataFrame(), {"input_rows": len(raw), "valid_rows": 0, "quality_score": 0.0}, str(exc)
    missing = [col for col in _REQUIRED_OHLC if col not in raw.columns]
    if missing:
        return pd.DataFrame(), {"input_rows": len(raw), "valid_rows": 0, "quality_score": 0.0}, (
            "Missing required column(s): " + ", ".join(missing) + ". Required columns: Date, Open, High, Low, Close. Volume is optional."
        )
    input_rows = len(raw)
    raw["Date"] = pd.to_datetime(raw["Date"], errors="coerce", utc=True).dt.tz_convert(None)
    numeric_cols = [c for c in ["Open", "High", "Low", "Close", "Adj Close", "Volume"] if c in raw.columns]
    for col in numeric_cols:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
        raw[col] = raw[col].where(np.isfinite(raw[col]))
    volume_column_missing = "Volume" not in raw.columns
    if volume_column_missing:
        raw["Volume"] = 0.0
        missing_volume_values = 0
        negative_volume_rows = 0
    else:
        missing_volume_values = int(raw["Volume"].isna().sum())
        negative_volume_rows = int((raw["Volume"] < 0).fillna(False).sum())
        raw.loc[raw["Volume"] < 0, "Volume"] = np.nan
    missing_required = raw["Date"].isna() | raw[["Open", "High", "Low", "Close"]].isna().any(axis=1)
    invalid_price = (raw[["Open", "High", "Low", "Close"]] <= 0).any(axis=1)
    invalid_ohlc = (raw["High"] < raw[["Open", "Low", "Close"]].max(axis=1)) | (raw["Low"] > raw[["Open", "High", "Close"]].min(axis=1))
    invalid_mask = missing_required | invalid_price | invalid_ohlc
    invalid_rows = int(invalid_mask.sum())
    raw = raw.loc[~invalid_mask].copy()
    raw["Volume"] = raw["Volume"].fillna(0)
    if "Adj Close" in raw.columns:
        raw["Adj Close"] = raw["Adj Close"].where(raw["Adj Close"] > 0)
    duplicate_count = int(raw.duplicated(subset=["Date"], keep="last").sum())
    raw = raw.sort_values("Date").drop_duplicates(subset=["Date"], keep="last")
    retained = [*OHLCV_COLUMNS]
    if "Adj Close" in raw.columns:
        retained.append("Adj Close")
    raw = raw.set_index("Date")[retained]
    raw.index.name = "Date"
    anomalies = negative_volume_rows + missing_volume_values
    report = {
        "input_rows": input_rows, "valid_rows": len(raw), "invalid_rows_removed": invalid_rows,
        "duplicate_dates_removed": duplicate_count, "negative_volume_rows": negative_volume_rows,
        "missing_volume_values": missing_volume_values, "volume_column_missing": volume_column_missing,
        "quality_score": _quality_score(input_rows, len(raw), anomalies),
        "date_start": raw.index.min() if len(raw) else None, "date_end": raw.index.max() if len(raw) else None,
    }
    if raw.empty:
        return raw, report, "No valid rows remain. Check dates, positive OHLC prices, and OHLC consistency."
    message = f"Validated {len(raw):,} rows from {source_name}; removed {invalid_rows} invalid OHLC rows and {duplicate_count} duplicate dates."
    if negative_volume_rows or missing_volume_values:
        message += f" Flagged {negative_volume_rows} negative and {missing_volume_values} missing/non-numeric volume values; these are set to zero for volume display."
    return raw, report, message


def _comparison_quality_report(input_rows: int, valid_rows: int, invalid_dates: int, invalid_values: int, duplicates: int, companies: int, coverage: dict | None = None) -> dict:
    anomalies = invalid_values
    return {
        "input_rows": input_rows, "valid_rows": valid_rows, "companies": companies,
        "invalid_rows_removed": invalid_dates, "invalid_price_values": invalid_values,
        "duplicate_dates_removed": duplicates, "quality_score": _quality_score(input_rows, valid_rows, anomalies),
        "coverage_by_company": coverage or {},
    }


def load_upload(uploaded_file: Any) -> tuple[str, pd.DataFrame, dict, str]:
    """Read upload and classify as single OHLCV or multi-company close-price matrix.

    Accepted comparison formats: Date/Ticker/Close (long) or Date + company columns (wide).
    """
    filename = getattr(uploaded_file, "name", "uploaded data")
    try:
        raw = _normalise_headers(_read_upload(uploaded_file))
    except Exception as exc:
        return "error", pd.DataFrame(), {}, f"Could not read {filename}: {exc}"
    if raw.empty:
        return "error", pd.DataFrame(), {}, "The uploaded file is empty."

    if "Date" in raw.columns and "Ticker" in raw.columns and "Close" in raw.columns and not all(c in raw.columns for c in ["Open", "High", "Low"]):
        frame = raw[["Date", "Ticker", "Close"]].copy()
        frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce", utc=True).dt.tz_convert(None)
        frame["Ticker"] = frame["Ticker"].where(frame["Ticker"].notna(), "").astype(str).str.strip().str.upper()
        frame["Close"] = pd.to_numeric(frame["Close"], errors="coerce")
        frame["Close"] = frame["Close"].where(np.isfinite(frame["Close"]))
        before = len(frame)
        frame = frame.dropna(subset=["Date", "Close"])
        frame = frame[(frame["Close"] > 0) & frame["Ticker"].ne("")]
        invalid_rows = before - len(frame)
        duplicates = int(frame.duplicated(["Date", "Ticker"], keep="last").sum())
        frame = frame.sort_values("Date").drop_duplicates(["Date", "Ticker"], keep="last")
        closes = frame.pivot(index="Date", columns="Ticker", values="Close").sort_index()
        closes = closes.dropna(axis=1, how="all")
        if closes.shape[1] < 2:
            return "error", pd.DataFrame(), {"input_rows": before, "valid_rows": len(frame), "invalid_rows_removed": invalid_rows, "duplicate_dates_removed": duplicates}, "Multi-company data needs at least two distinct tickers with valid closing prices."
        coverage = {str(c): int(closes[c].notna().sum()) for c in closes.columns}
        report = _comparison_quality_report(before, len(frame), invalid_rows, 0, duplicates, closes.shape[1], coverage)
        return "comparison", closes, report, f"Loaded {closes.shape[1]} companies across {len(closes):,} dates from {filename}; removed {invalid_rows} invalid rows and {duplicates} duplicate ticker/date rows."

    if "Date" in raw.columns:
        non_date_cols = [c for c in raw.columns if c != "Date"]
        if len(non_date_cols) >= 2 and not any(c in raw.columns for c in ["Open", "High", "Low"]):
            input_rows = len(raw)
            raw["Date"] = pd.to_datetime(raw["Date"], errors="coerce", utc=True).dt.tz_convert(None)
            for col in non_date_cols:
                raw[col] = pd.to_numeric(raw[col], errors="coerce")
                raw[col] = raw[col].where(np.isfinite(raw[col]))
            invalid_dates = int(raw["Date"].isna().sum())
            raw = raw.dropna(subset=["Date"]).sort_values("Date")
            duplicates = int(raw.duplicated(subset=["Date"], keep="last").sum())
            raw = raw.drop_duplicates("Date", keep="last").set_index("Date")
            closes = raw[non_date_cols].where(raw[non_date_cols] > 0)
            invalid_values = int(closes.isna().sum().sum())
            closes = closes.dropna(axis=1, how="all")
            if closes.shape[1] >= 2:
                coverage = {str(c): int(closes[c].notna().sum()) for c in closes.columns}
                report = _comparison_quality_report(input_rows, len(raw), invalid_dates, invalid_values, duplicates, closes.shape[1], coverage)
                message = f"Loaded {closes.shape[1]} company series from {filename}; {invalid_dates} invalid dates, {invalid_values} invalid/missing price cells and {duplicates} duplicate dates were identified."
                return "comparison", closes, report, message
            return "error", pd.DataFrame(), _comparison_quality_report(input_rows, len(raw), invalid_dates, invalid_values, duplicates, closes.shape[1]), "Wide-format comparison data needs at least two columns with valid positive closing prices after validation."

    cleaned, report, message = validate_ohlcv_frame(raw, filename)
    if cleaned.empty:
        return "error", cleaned, report, message
    report.update({"source_name": filename, "is_upload": True})
    return "single", cleaned, report, message
