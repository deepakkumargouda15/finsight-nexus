import numpy as np
import pandas as pd
from src.analytics import calculate_metrics, normalized_performance, drawdown_series, generate_insights, make_synthetic_comparison


def test_metrics_are_correct_for_known_series():
    idx = pd.date_range("2025-01-01", periods=4, freq="D")
    prices = pd.DataFrame({"AAA": [100, 110, 99, 121]}, index=idx)
    metrics = calculate_metrics(prices, periods_per_year=3)
    assert round(metrics.loc["AAA", "Total Return (%)"], 6) == 21.0
    assert round(metrics.loc["AAA", "Maximum Drawdown (%)"], 6) == -10.0


def test_normalized_performance_starts_at_100():
    prices = pd.DataFrame({"A": [10, 12], "B": [20, 18]}, index=pd.date_range("2025-01-01", periods=2))
    normalized = normalized_performance(prices)
    assert np.allclose(normalized.iloc[0].values, [100, 100])


def test_insights_and_synthetic_demo_are_explicitly_demonstrative():
    demo = make_synthetic_comparison(rows=30)
    metrics = calculate_metrics(demo)
    insights = generate_insights(metrics, demo)
    assert demo.shape == (30, 5)
    assert any("not forecasts" in line.lower() for line in insights)


def test_annualized_return_uses_elapsed_calendar_time():
    prices = pd.DataFrame({"AAA": [100.0, 200.0]}, index=pd.to_datetime(["2024-01-01", "2025-01-01"]))
    metrics = calculate_metrics(prices)
    assert 99.0 <= metrics.loc["AAA", "Annualized Return (%)"] <= 101.0


def test_risk_free_rate_changes_sharpe_ratio():
    idx = pd.date_range("2024-01-01", periods=100, freq="B")
    prices = pd.DataFrame({"AAA": np.cumprod(1 + np.tile([0.01, -0.003, 0.006, -0.001], 25)) * 100}, index=idx)
    zero_rf = calculate_metrics(prices, risk_free_rate=0.0)
    positive_rf = calculate_metrics(prices, risk_free_rate=0.05)
    assert positive_rf.loc["AAA", "Sharpe Ratio"] < zero_rf.loc["AAA", "Sharpe Ratio"]


def test_benchmark_relative_metrics_include_expected_fields():
    from src.analytics import benchmark_relative_metrics
    idx = pd.date_range("2024-01-01", periods=40, freq="B")
    benchmark = np.cumprod(1 + np.linspace(-0.01, 0.012, len(idx))) * 100
    prices = pd.DataFrame({"BENCH": benchmark, "PEER": benchmark * np.cumprod(1 + np.sin(np.arange(len(idx))) * 0.001)}, index=idx)
    result = benchmark_relative_metrics(prices, "BENCH")
    assert "PEER" in result.index
    assert {"Beta", "Excess Total Return (pp)", "Tracking Error (%)", "Information Ratio"}.issubset(result.columns)


def test_analytics_brief_contains_period_source_and_limitations():
    from src.analytics import create_analytics_brief
    prices = make_synthetic_comparison(rows=40)
    metrics = calculate_metrics(prices)
    brief = create_analytics_brief(metrics, prices, "fictional test data", risk_free_rate=0.02, benchmark="DEMO_ALPHA")
    assert "fictional test data" in brief
    assert "Benchmark-relative analysis" in brief
    assert "not investment advice" in brief.lower()
