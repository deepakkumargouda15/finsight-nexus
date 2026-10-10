import io
import pandas as pd
from src.ingestion import validate_ohlcv_frame, load_upload

class Upload:
    def __init__(self, name, content):
        self.name = name
        self._content = content
    def getvalue(self):
        return self._content


def test_valid_ohlcv_and_duplicate_date_cleanup():
    frame = pd.DataFrame({
        "date": ["2025-01-02", "2025-01-01", "2025-01-01"],
        "open": [10, 9, 9.5], "high": [11, 10, 10.5], "low": [9, 8, 9],
        "close": [10.5, 9.5, 10], "volume": [100, 90, 110],
    })
    cleaned, report, message = validate_ohlcv_frame(frame, "test.csv")
    assert len(cleaned) == 2
    assert cleaned.index.is_monotonic_increasing
    assert report["duplicate_dates_removed"] == 1
    assert "Validated" in message


def test_missing_required_columns_returns_actionable_message():
    cleaned, report, message = validate_ohlcv_frame(pd.DataFrame({"Date": ["2025-01-01"], "Close": [10]}))
    assert cleaned.empty
    assert "Open" in message and "High" in message


def test_long_format_upload_becomes_comparison_matrix():
    content = b"Date,Ticker,Close\n2025-01-01,AAA,100\n2025-01-01,BBB,50\n2025-01-02,AAA,102\n2025-01-02,BBB,51\n2025-01-03,AAA,101\n2025-01-03,BBB,52\n"
    kind, frame, report, message = load_upload(Upload("comparison.csv", content))
    assert kind == "comparison"
    assert list(frame.columns) == ["AAA", "BBB"]
    assert frame.shape == (3, 2)


def test_wide_format_upload_becomes_comparison_matrix():
    content = b"Date,AAPL,MSFT,GOOGL\n2025-01-01,100,200,300\n2025-01-02,102,198,303\n2025-01-03,101,201,306\n"
    kind, frame, report, message = load_upload(Upload("wide.csv", content))
    assert kind == "comparison"
    assert frame.shape == (3, 3)


def test_single_company_csv_upload_returns_clean_ohlcv():
    content = b"Date,Open,High,Low,Close,Volume\n2025-01-01,10,11,9,10.5,100\n2025-01-02,10.5,12,10,11.5,120\n2025-01-03,11.5,12.5,11,12,140\n"
    kind, frame, report, message = load_upload(Upload("prices.csv", content))
    assert kind == "single"
    assert list(frame.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert len(frame) == 3
    assert report["valid_rows"] == 3


def test_adjusted_close_is_preserved_as_separate_column():
    frame = pd.DataFrame({
        "Date": ["2025-01-01", "2025-01-02"], "Open": [10, 11], "High": [11, 12],
        "Low": [9, 10], "Close": [10.5, 11.5], "Adj Close": [10.2, 11.2],
    })
    cleaned, report, message = validate_ohlcv_frame(frame)
    assert "Close" in cleaned and "Adj Close" in cleaned
    assert cleaned["Close"].iloc[0] == 10.5
    assert cleaned["Adj Close"].iloc[0] == 10.2


def test_duplicate_normalized_headers_are_rejected_clearly():
    frame = pd.DataFrame({"Date": ["2025-01-01"], "Open": [10], "open": [10], "High": [11], "Low": [9], "Close": [10.5]})
    cleaned, report, message = validate_ohlcv_frame(frame)
    assert cleaned.empty
    assert "Duplicate columns" in message


def test_negative_volume_is_reported_instead_of_silently_clipped():
    frame = pd.DataFrame({
        "Date": ["2025-01-01", "2025-01-02"], "Open": [10, 10], "High": [11, 12],
        "Low": [9, 9], "Close": [10.5, 11], "Volume": [100, -2],
    })
    cleaned, report, message = validate_ohlcv_frame(frame)
    assert len(cleaned) == 2
    assert report["negative_volume_rows"] == 1
    assert cleaned["Volume"].iloc[1] == 0
    assert "negative" in message.lower()
