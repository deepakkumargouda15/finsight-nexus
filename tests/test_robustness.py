import io
import numpy as np
import pandas as pd

from src.analytics import calculate_metrics, infer_periods_per_year, make_synthetic_ohlcv
from src.ingestion import load_upload, validate_ohlcv_frame


class Upload:
    def __init__(self, name, content):
        self.name = name
        self._content = content

    def getvalue(self):
        return self._content


def test_synthetic_ohlcv_is_valid_and_explicitly_fictional_shape():
    frame = make_synthetic_ohlcv(seed=3, rows=80)
    assert frame.shape == (80, 5)
    assert list(frame.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert (frame[["Open", "High", "Low", "Close"]] > 0).all().all()
    assert (frame["High"] >= frame[["Open", "Low", "Close"]].max(axis=1)).all()
    assert (frame["Low"] <= frame[["Open", "High", "Close"]].min(axis=1)).all()
    assert (frame["Volume"] >= 0).all()


def test_ohlcv_rejects_infinite_and_inconsistent_prices():
    raw = pd.DataFrame({
        "Date": ["2025-01-01", "2025-01-02", "2025-01-03"],
        "Open": [10, np.inf, 10],
        "High": [12, 12, 9],
        "Low": [9, 9, 8],
        "Close": [11, 11, 10],
    })
    cleaned, report, _ = validate_ohlcv_frame(raw)
    assert len(cleaned) == 1
    assert report["invalid_rows_removed"] == 2


def test_xlsx_upload_is_supported():
    buffer = io.BytesIO()
    pd.DataFrame({
        "Date": ["2025-01-01", "2025-01-02", "2025-01-03"],
        "Open": [10, 11, 12], "High": [11, 12, 13],
        "Low": [9, 10, 11], "Close": [10.5, 11.5, 12.5],
    }).to_excel(buffer, index=False)
    kind, frame, report, message = load_upload(Upload("prices.xlsx", buffer.getvalue()))
    assert kind == "single"
    assert len(frame) == 3
    assert "Validated" in message


def test_long_format_reports_duplicate_ticker_date_rows():
    content = (
        b"Date,Ticker,Close\n"
        b"2025-01-01,AAA,100\n2025-01-01,AAA,101\n"
        b"2025-01-01,BBB,50\n2025-01-02,AAA,102\n2025-01-02,BBB,51\n"
        b"2025-01-03,AAA,103\n2025-01-03,BBB,52\n"
    )
    kind, frame, report, _ = load_upload(Upload("prices.csv", content))
    assert kind == "comparison"
    assert report["duplicate_dates_removed"] == 1
    assert frame.loc[pd.Timestamp("2025-01-01"), "AAA"] == 101


def test_metric_calculation_handles_constant_prices_without_infinite_sharpe():
    prices = pd.DataFrame({"FLAT": [10, 10, 10, 10]}, index=pd.date_range("2025-01-01", periods=4))
    metrics = calculate_metrics(prices, periods_per_year=252)
    assert metrics.loc["FLAT", "Total Return (%)"] == 0
    assert pd.isna(metrics.loc["FLAT", "Sharpe Ratio"])


def test_frequency_inference_for_monthly_data():
    monthly = pd.date_range("2024-01-31", periods=8, freq="ME")
    assert infer_periods_per_year(monthly) == 12
