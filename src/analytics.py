"""Financial analytics for historical price series.

Metrics are descriptive, not forecasts. All annualization assumptions are explicit
and callers can pass an annual risk-free rate as a decimal (e.g. 0.04 for 4%).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def infer_periods_per_year(index) -> int:
    """Infer approximate observations/year from timestamps; daily defaults to 252."""
    idx = pd.DatetimeIndex(pd.to_datetime(index, errors="coerce")).dropna().sort_values().unique()
    if len(idx) < 3:
        return 252
    deltas = pd.Series(idx).diff().dt.total_seconds().div(86400).dropna()
    median_days = float(deltas.median()) if not deltas.empty else 1.0
    if median_days >= 25:
        return 12
    if median_days >= 5:
        return 52
    return 252


def _clean_prices(close_prices: pd.DataFrame | pd.Series) -> pd.DataFrame:
    if isinstance(close_prices, pd.Series):
        close_prices = close_prices.to_frame(name=close_prices.name or "Series")
    if close_prices is None or close_prices.empty:
        return pd.DataFrame()
    prices = close_prices.copy()
    prices.index = pd.to_datetime(prices.index, errors="coerce")
    prices = prices.loc[~prices.index.isna()].sort_index()
    prices = prices.apply(pd.to_numeric, errors="coerce")
    prices = prices.where(np.isfinite(prices) & (prices > 0))
    prices = prices[~prices.index.duplicated(keep="last")]
    return prices.dropna(axis=1, how="all")


def calculate_metrics(
    close_prices: pd.DataFrame | pd.Series,
    periods_per_year: int | None = None,
    risk_free_rate: float = 0.0,
) -> pd.DataFrame:
    """Calculate performance and risk metrics. risk_free_rate is an annual decimal."""
    prices = _clean_prices(close_prices)
    if prices.empty:
        return pd.DataFrame()
    ppy = max(int(periods_per_year or infer_periods_per_year(prices.index)), 1)
    if risk_free_rate <= -1:
        raise ValueError("Annual risk-free rate must be greater than -100%.")
    periodic_rf = (1 + float(risk_free_rate)) ** (1 / ppy) - 1
    rows = []
    for name in prices.columns:
        series = prices[name].dropna()
        if len(series) < 2:
            continue
        returns = series.pct_change().dropna()
        total_return = series.iloc[-1] / series.iloc[0] - 1
        elapsed_years = max((series.index[-1] - series.index[0]).total_seconds() / (365.25 * 86400), 0)
        annualized_return = ((series.iloc[-1] / series.iloc[0]) ** (1 / elapsed_years) - 1) if elapsed_years > 0 else np.nan
        volatility_periodic = returns.std(ddof=1) if len(returns) > 1 else np.nan
        volatility = volatility_periodic * np.sqrt(ppy) if pd.notna(volatility_periodic) else np.nan
        excess_returns = returns - periodic_rf
        excess_std = excess_returns.std(ddof=1) if len(excess_returns) > 1 else np.nan
        sharpe = (excess_returns.mean() / volatility_periodic * np.sqrt(ppy)) if pd.notna(volatility_periodic) and volatility_periodic > 0 else np.nan
        drawdown = (series / series.cummax() - 1) * 100
        rows.append({
            "Company": str(name),
            "Observations": int(len(series)),
            "Start Date": series.index[0].date().isoformat(),
            "End Date": series.index[-1].date().isoformat(),
            "Latest Close": float(series.iloc[-1]),
            "Total Return (%)": total_return * 100,
            "Annualized Return (%)": annualized_return * 100 if pd.notna(annualized_return) else np.nan,
            "Annualized Volatility (%)": volatility * 100 if pd.notna(volatility) else np.nan,
            "Maximum Drawdown (%)": float(drawdown.min()),
            "Best Period (%)": float(returns.max() * 100) if len(returns) else np.nan,
            "Worst Period (%)": float(returns.min() * 100) if len(returns) else np.nan,
            "Sharpe Ratio": float(sharpe) if pd.notna(sharpe) else np.nan,
            "Risk-free Rate (%)": float(risk_free_rate * 100),
        })
    return pd.DataFrame(rows).set_index("Company") if rows else pd.DataFrame()


def benchmark_relative_metrics(close_prices: pd.DataFrame, benchmark: str, periods_per_year: int | None = None, risk_free_rate: float = 0.0) -> pd.DataFrame:
    """Compute excess return, beta, alpha, tracking error, information ratio and correlation.

    Only shared valid dates are used. Alpha is a simple annualized CAPM-style estimate,
    not a regression forecast; this is documented in the UI and methodology.
    """
    prices = _clean_prices(close_prices)
    if benchmark not in prices.columns:
        return pd.DataFrame()
    peers = prices.drop(columns=[benchmark]).dropna(axis=1, how="all")
    rows = []
    ppy = max(int(periods_per_year or infer_periods_per_year(prices.index)), 1)
    for name in peers.columns:
        pair = pd.concat([peers[name].rename("asset"), prices[benchmark].rename("benchmark")], axis=1).dropna()
        if len(pair) < 4:
            continue
        asset_returns = pair["asset"].pct_change().dropna()
        benchmark_returns = pair["benchmark"].pct_change().dropna()
        returns = pd.concat([asset_returns.rename("asset"), benchmark_returns.rename("benchmark")], axis=1).dropna()
        if len(returns) < 3:
            continue
        variance = returns["benchmark"].var(ddof=1)
        beta = returns["asset"].cov(returns["benchmark"]) / variance if pd.notna(variance) and variance > 0 else np.nan
        active = returns["asset"] - returns["benchmark"]
        tracking_error = active.std(ddof=1) * np.sqrt(ppy) if len(active) > 1 else np.nan
        information_ratio = active.mean() / active.std(ddof=1) * np.sqrt(ppy) if len(active) > 1 and active.std(ddof=1) > 0 else np.nan
        asset_total = pair["asset"].iloc[-1] / pair["asset"].iloc[0] - 1
        bench_total = pair["benchmark"].iloc[-1] / pair["benchmark"].iloc[0] - 1
        years = max((pair.index[-1] - pair.index[0]).total_seconds() / (365.25 * 86400), 0)
        asset_ann = (pair["asset"].iloc[-1] / pair["asset"].iloc[0]) ** (1 / years) - 1 if years > 0 else np.nan
        bench_ann = (pair["benchmark"].iloc[-1] / pair["benchmark"].iloc[0]) ** (1 / years) - 1 if years > 0 else np.nan
        alpha = asset_ann - (risk_free_rate + beta * (bench_ann - risk_free_rate)) if pd.notna(beta) and pd.notna(asset_ann) and pd.notna(bench_ann) else np.nan
        rows.append({
            "Company": name,
            "Benchmark": benchmark,
            "Shared Observations": len(pair),
            "Excess Total Return (pp)": (asset_total - bench_total) * 100,
            "Beta": beta,
            "Annualized Alpha Estimate (%)": alpha * 100 if pd.notna(alpha) else np.nan,
            "Tracking Error (%)": tracking_error * 100 if pd.notna(tracking_error) else np.nan,
            "Information Ratio": information_ratio,
            "Return Correlation": returns["asset"].corr(returns["benchmark"]),
        })
    return pd.DataFrame(rows).set_index("Company") if rows else pd.DataFrame()


def normalized_performance(close_prices: pd.DataFrame) -> pd.DataFrame:
    prices = _clean_prices(close_prices)
    first = prices.apply(lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan)
    return prices.divide(first, axis=1) * 100


def drawdown_series(close_prices: pd.DataFrame) -> pd.DataFrame:
    prices = _clean_prices(close_prices)
    return (prices / prices.cummax() - 1) * 100


def generate_insights(metrics: pd.DataFrame, close_prices: pd.DataFrame) -> list[str]:
    """Generate descriptive observations grounded in calculated metrics."""
    if metrics is None or metrics.empty:
        return ["Not enough valid observations to calculate meaningful comparison insights."]
    insights = []
    total = metrics["Total Return (%)"].dropna()
    vol = metrics["Annualized Volatility (%)"].dropna()
    dd = metrics["Maximum Drawdown (%)"].dropna()
    if not total.empty:
        best, worst = total.idxmax(), total.idxmin()
        insights.append(f"**Strongest total performance:** {best} returned {total.loc[best]:+.2f}% over the available comparison window.")
        if best != worst:
            insights.append(f"**Weakest total performance:** {worst} returned {total.loc[worst]:+.2f}% over the same window.")
    if not vol.empty:
        high, low = vol.idxmax(), vol.idxmin()
        insights.append(f"**Risk variation:** {high} had the highest annualized volatility ({vol.loc[high]:.2f}%), while {low} had the lowest ({vol.loc[low]:.2f}%). Volatility measures variability, not direction.")
    if not dd.empty:
        worst_dd = dd.idxmin()
        insights.append(f"**Largest peak-to-trough decline:** {worst_dd} recorded a maximum drawdown of {dd.loc[worst_dd]:.2f}% during the selected window.")
    aligned_returns = _clean_prices(close_prices).pct_change().dropna(how="all")
    if aligned_returns.shape[1] >= 2 and len(aligned_returns) >= 3:
        corr = aligned_returns.corr(min_periods=3)
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack().dropna()
        if not upper.empty:
            pair = upper.abs().idxmax()
            insights.append(f"**Most closely co-moving pair:** {pair[0]} and {pair[1]} had a return correlation of {upper.loc[pair]:+.2f}. Correlation does not establish causation.")
    insights.append("These observations describe the selected historical dataset; they are not forecasts or investment advice. Results depend on data quality, date coverage, currency and annualization assumptions.")
    return insights


def create_analytics_brief(metrics: pd.DataFrame, prices: pd.DataFrame, source_note: str, risk_free_rate: float = 0.0, benchmark: str | None = None) -> str:
    """Create a reproducible, downloadable Markdown report from calculated metrics."""
    if metrics is None or metrics.empty:
        return "# FinSight Nexus Analytics Brief\n\nNot enough valid data to produce a report."
    start, end = pd.to_datetime(prices.index).min().date(), pd.to_datetime(prices.index).max().date()
    lines = [
        "# FinSight Nexus — Analytics Brief", "", f"**Analysis period:** {start} to {end}",
        f"**Data source:** {source_note or 'Not specified'}", f"**Annual risk-free rate assumption:** {risk_free_rate * 100:.2f}%",
        f"**Companies / series:** {len(metrics)}", "", "## Executive summary", "",
    ]
    returns = metrics["Total Return (%)"].dropna()
    vols = metrics["Annualized Volatility (%)"].dropna()
    dds = metrics["Maximum Drawdown (%)"].dropna()
    if not returns.empty:
        lines.append(f"- Highest total return: **{returns.idxmax()}** ({returns.max():+.2f}%).")
        lines.append(f"- Lowest total return: **{returns.idxmin()}** ({returns.min():+.2f}%).")
    if not vols.empty:
        lines.append(f"- Highest annualized volatility: **{vols.idxmax()}** ({vols.max():.2f}%).")
    if not dds.empty:
        lines.append(f"- Largest maximum drawdown: **{dds.idxmin()}** ({dds.min():.2f}%).")
    lines += ["", "## Company metrics", "", metrics.round(4).to_markdown(), ""]
    if benchmark and benchmark in prices.columns:
        rel = benchmark_relative_metrics(prices, benchmark, risk_free_rate=risk_free_rate)
        lines += [f"## Benchmark-relative analysis — {benchmark}", "", rel.round(4).to_markdown() if not rel.empty else "Not enough shared observations to calculate benchmark-relative metrics.", ""]
    lines += [
        "## Methodology and caveats", "",
        "- Total return uses the first and last available close in the analyzed window.",
        "- Annualized return uses elapsed calendar time between the first and last observation.",
        "- Annualized volatility and Sharpe ratio use an inferred observation frequency (daily ≈ 252, weekly ≈ 52, monthly ≈ 12 periods/year).",
        "- Sharpe ratio uses the selected annual risk-free rate converted to a periodic rate.",
        "- Maximum drawdown is the largest decline from a running historical peak.",
        "- Benchmark alpha is a simple annualized CAPM-style estimate; it is not a regression forecast.",
        "- Uploaded data is not independently verified; synthetic data is fictional; live provider data may be delayed or incomplete.",
        "- Currency, dividends, corporate actions, market calendars and stale/missing observations can affect comparisons.",
        "- Historical performance is descriptive and is not investment advice or a forecast.",
        "", "---", "Generated by FinSight Nexus — independent educational portfolio project; not an LSEG product.",
    ]
    return "\n".join(lines)


def make_synthetic_ohlcv(seed: int = 29, rows: int = 260) -> pd.DataFrame:
    """Create fictional OHLCV data for an offline demonstration."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=rows)
    close = 100 * np.cumprod(1 + rng.normal(0.00025, 0.014, rows))
    previous = np.r_[close[0], close[:-1]]
    open_prices = previous * (1 + rng.normal(0, 0.004, rows))
    high = np.maximum(open_prices, close) * (1 + rng.uniform(0.001, 0.012, rows))
    low = np.minimum(open_prices, close) * (1 - rng.uniform(0.001, 0.012, rows))
    volume = rng.integers(250_000, 2_500_000, rows)
    frame = pd.DataFrame({"Open": open_prices, "High": high, "Low": low, "Close": close, "Volume": volume}, index=dates)
    frame.index.name = "Date"
    return frame


def make_synthetic_comparison(seed: int = 17, rows: int = 260) -> pd.DataFrame:
    """Create fictional price series for offline UI demonstrations."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=rows)
    names = ["DEMO_ALPHA", "DEMO_BETA", "DEMO_GAMMA", "DEMO_DELTA", "DEMO_EPSILON"]
    drifts = [0.00045, 0.00025, 0.00010, 0.00035, -0.00005]
    vols = [0.012, 0.008, 0.018, 0.014, 0.022]
    data = {name: (100 + i * 20) * np.cumprod(1 + rng.normal(drifts[i], vols[i], rows)) for i, name in enumerate(names)}
    return pd.DataFrame(data, index=dates).rename_axis("Date")
