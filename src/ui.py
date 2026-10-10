"""Reusable Streamlit presentation components for FinSight Nexus."""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.analytics import (
    calculate_metrics, normalized_performance, drawdown_series, generate_insights,
    infer_periods_per_year, benchmark_relative_metrics, create_analytics_brief,
)
from src.helpers import compute_indicators


def render_quality_report(report: dict):
    if not report:
        return
    st.markdown("#### Data quality scorecard")
    score = report.get("quality_score")
    if score is not None:
        st.progress(min(max(float(score) / 100, 0), 1), text=f"Quality score: {score:.1f}/100 (structural checks only; not source verification)")
    cols = st.columns(4)
    cols[0].metric("Input rows", f"{report.get('input_rows', '—'):,}" if isinstance(report.get("input_rows"), (int, np.integer)) else "—")
    cols[1].metric("Valid rows", f"{report.get('valid_rows', '—'):,}" if isinstance(report.get("valid_rows"), (int, np.integer)) else "—")
    cols[2].metric("Invalid rows / dates", f"{report.get('invalid_rows_removed', 0):,}")
    cols[3].metric("Duplicate dates / keys", f"{report.get('duplicate_dates_removed', 0):,}")
    extra = []
    if report.get("negative_volume_rows"):
        extra.append(f"Negative volume rows: {report['negative_volume_rows']}")
    if report.get("missing_volume_values"):
        extra.append(f"Missing/non-numeric volume values: {report['missing_volume_values']}")
    if report.get("volume_column_missing"):
        extra.append("Volume column not supplied (optional)")
    if report.get("invalid_price_values"):
        extra.append(f"Invalid/missing price cells: {report['invalid_price_values']}")
    if report.get("date_start") is not None and report.get("date_end") is not None:
        extra.append(f"Date coverage: {pd.Timestamp(report['date_start']).date()} to {pd.Timestamp(report['date_end']).date()}")
    if extra:
        st.caption(" · ".join(extra))
    if report.get("coverage_by_company"):
        coverage = pd.DataFrame([{"Company": k, "Valid price observations": v} for k, v in report["coverage_by_company"].items()])
        st.dataframe(coverage, hide_index=True, use_container_width=True)


def render_single_company(df, info, title, allow_download=True):
    if df is None or df.empty or "Close" not in df.columns:
        st.warning("No usable price data is available for this view.")
        return
    original_df = df.copy()
    basis = "Close"
    if "Adj Close" in df.columns and df["Adj Close"].notna().sum() >= 2:
        basis = st.radio("Price basis", ["Close", "Adj Close"], horizontal=True,
                         help="Adjusted Close can account for distributions and splits in some provider datasets. Confirm the source's adjustment methodology.")
    analysis_df = df.copy()
    if basis == "Adj Close":
        analysis_df["Close"] = pd.to_numeric(analysis_df["Adj Close"], errors="coerce")
    analysis_df = compute_indicators(analysis_df)
    close = pd.to_numeric(analysis_df["Close"], errors="coerce").dropna()
    if len(close) < 2:
        st.warning("At least two valid closing prices are required for performance metrics.")
        return
    risk_free_pct = st.number_input("Annual risk-free rate assumption (%)", min_value=-5.0, max_value=25.0, value=0.0, step=0.25, key=f"single_rf_{str(title)}")
    metrics = calculate_metrics(close.rename(str(title)), risk_free_rate=risk_free_pct / 100)
    if (close.index[-1] - close.index[0]).days < 30:
        st.warning("This price history spans less than 30 calendar days. Annualized return and risk estimates can be unstable on short windows.")
    metric_row = metrics.iloc[0]
    volatility = metric_row.get("Annualized Volatility (%)", np.nan)
    drawdown = metric_row.get("Maximum Drawdown (%)", np.nan)
    total_return = metric_row.get("Total Return (%)", np.nan)
    latest = close.iloc[-1]
    k = st.columns(4)
    k[0].metric("Latest close", f"{latest:,.2f}", f"{total_return:+.2f}% total return" if pd.notna(total_return) else None)
    k[1].metric("Annualized volatility", f"{volatility:.2f}%" if pd.notna(volatility) else "N/A")
    k[2].metric("Maximum drawdown", f"{drawdown:.2f}%" if pd.notna(drawdown) else "N/A")
    k[3].metric("Observations", f"{len(close):,}")
    st.caption(f"Price basis: {basis}. Annualization inferred from date spacing (daily≈252, weekly≈52, monthly≈12 periods/year). Values are descriptive, not forecasts.")
    tabs = st.tabs(["Performance", "Technical indicators", "Data & quality"])
    with tabs[0]:
        chart = go.Figure()
        chart.add_trace(go.Scatter(x=analysis_df.index, y=analysis_df["Close"], mode="lines", name=basis, line={"width": 2.5}))
        for column, label in [("MA50", "MA 50"), ("MA200", "MA 200")]:
            if column in analysis_df:
                chart.add_trace(go.Scatter(x=analysis_df.index, y=analysis_df[column], mode="lines", name=label))
        chart.update_layout(title="Closing price and moving averages", xaxis_title="Date", yaxis_title="Price (source currency not inferred)", hovermode="x unified", legend_title="Series")
        st.plotly_chart(chart, use_container_width=True)
        volume = go.Figure(go.Bar(x=analysis_df.index, y=analysis_df["Volume"], name="Volume"))
        volume.update_layout(title="Trading volume", xaxis_title="Date", yaxis_title="Volume")
        st.plotly_chart(volume, use_container_width=True)
        st.markdown("#### What the metrics say")
        for insight in generate_insights(metrics, close.to_frame(str(title))):
            st.markdown(f"- {insight}")
        brief = create_analytics_brief(metrics, close.to_frame(str(title)), info.get("data_source", "Not specified"), risk_free_rate=risk_free_pct / 100)
        st.download_button("Download analytics brief (Markdown)", brief.encode("utf-8"), file_name="finsight_analytics_brief.md", mime="text/markdown")
    with tabs[1]:
        left, right = st.columns(2)
        with left:
            fig = go.Figure(go.Scatter(x=analysis_df.index, y=analysis_df["RSI14"], name="RSI (14)"))
            fig.add_hline(y=70, line_dash="dash", annotation_text="70")
            fig.add_hline(y=30, line_dash="dash", annotation_text="30")
            fig.update_layout(title="Relative Strength Index", yaxis={"range": [0, 100]})
            st.plotly_chart(fig, use_container_width=True)
        with right:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=analysis_df.index, y=analysis_df["MACD"], name="MACD"))
            fig.add_trace(go.Scatter(x=analysis_df.index, y=analysis_df["MACD_Signal"], name="Signal"))
            fig.add_trace(go.Bar(x=analysis_df.index, y=analysis_df["MACD_Histogram"], name="Histogram"))
            fig.update_layout(title="MACD momentum indicator")
            st.plotly_chart(fig, use_container_width=True)
        st.caption("Technical indicators summarize historical price patterns. They are not standalone trading signals.")
    with tabs[2]:
        render_quality_report(info.get("quality_report", {}))
        st.dataframe(original_df.tail(100), use_container_width=True)
        if allow_download:
            st.download_button("Download cleaned data (CSV)", original_df.to_csv(index=True).encode("utf-8"), file_name=f"{str(title).replace(' ', '_')}_cleaned.csv", mime="text/csv")
        st.caption(f"Data source: {info.get('data_source', 'Not specified')}")


def render_comparison(close_prices: pd.DataFrame, title="Multi-company comparison", source_note=""):
    if close_prices is None or close_prices.empty:
        st.warning("No comparison data is available. Load at least two usable company price series.")
        return
    prices = close_prices.copy()
    prices.index = pd.to_datetime(prices.index, errors="coerce")
    prices = prices.loc[~prices.index.isna()].sort_index()
    prices = prices.apply(pd.to_numeric, errors="coerce").where(lambda x: np.isfinite(x) & (x > 0))
    prices = prices.dropna(axis=1, how="all").dropna(how="all")
    if prices.shape[1] < 2 or len(prices) < 4:
        st.warning("Comparison requires at least two companies and four dates with usable prices.")
        return
    st.subheader(title)
    if source_note:
        st.caption(source_note)
    st.info("Comparisons assume all selected series are expressed in a comparable currency and reflect comparable price adjustments. Currency conversion and exchange-calendar normalization are not performed automatically.")
    risk_free_pct = st.number_input("Annual risk-free rate assumption (%)", min_value=-5.0, max_value=25.0, value=0.0, step=0.25,
                                    help="Used in Sharpe and benchmark-alpha calculations. Set this to a defensible annual rate for your analysis; zero is only a default assumption.")
    risk_free_rate = risk_free_pct / 100
    benchmark_options = ["None"] + [str(c) for c in prices.columns]
    benchmark = st.selectbox("Benchmark series (optional)", benchmark_options, index=0,
                             help="Choose one series from the dataset as a comparison benchmark. This does not make it an official market index.")
    aligned = prices.dropna(how="any")
    if len(aligned) < 4:
        st.warning(f"Only {len(aligned)} dates are shared by every series. At least four shared dates are required for comparable analysis. Review the data-quality report or upload overlapping date ranges.")
        st.markdown("#### Available price coverage")
        st.dataframe(pd.DataFrame({"Valid observations": prices.notna().sum(), "First date": prices.apply(lambda s: s.first_valid_index()), "Last date": prices.apply(lambda s: s.last_valid_index())}), use_container_width=True)
        return
    prices_for_metrics = aligned
    st.caption(f"All metrics use {len(aligned):,} shared dates ({aligned.index.min().date()} to {aligned.index.max().date()}); this avoids comparing different date windows.")
    if (aligned.index[-1] - aligned.index[0]).days < 30:
        st.warning("The shared history spans less than 30 calendar days. Annualized return and risk estimates can be unstable on short windows.")
    metrics = calculate_metrics(prices_for_metrics, risk_free_rate=risk_free_rate)
    if metrics.empty:
        st.warning("There are not enough valid prices to calculate comparison metrics.")
        return
    top = st.columns(4)
    top[0].metric("Companies / series", str(prices_for_metrics.shape[1]))
    top[1].metric("Shared dates", f"{len(prices_for_metrics):,}")
    best = metrics["Total Return (%)"].idxmax()
    top[2].metric("Highest total return", best, f"{metrics.loc[best, 'Total Return (%)']:+.2f}%")
    top[3].metric("Annual risk-free assumption", f"{risk_free_pct:.2f}%")
    tabs = st.tabs(["Performance", "Risk & metrics", "Benchmark analysis", "Correlation", "Insights & report"])
    with tabs[0]:
        indexed = normalized_performance(prices_for_metrics)
        fig = go.Figure()
        for col in indexed:
            fig.add_trace(go.Scatter(x=indexed.index, y=indexed[col], mode="lines", name=str(col)))
        fig.update_layout(title="Growth of 100 units (rebased to first shared date)", xaxis_title="Date", yaxis_title="Indexed value", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        dd = drawdown_series(prices_for_metrics)
        fig2 = go.Figure()
        for col in dd:
            fig2.add_trace(go.Scatter(x=dd.index, y=dd[col], mode="lines", name=str(col)))
        fig2.update_layout(title="Peak-to-trough drawdown", xaxis_title="Date", yaxis_title="Drawdown (%)", hovermode="x unified")
        st.plotly_chart(fig2, use_container_width=True)
    with tabs[1]:
        st.dataframe(metrics.style.format({
            "Latest Close": "{:,.2f}", "Total Return (%)": "{:+.2f}%", "Annualized Return (%)": "{:+.2f}%",
            "Annualized Volatility (%)": "{:.2f}%", "Maximum Drawdown (%)": "{:.2f}%", "Best Period (%)": "{:+.2f}%",
            "Worst Period (%)": "{:+.2f}%", "Sharpe Ratio": "{:.2f}",
        }, na_rep="N/A"), use_container_width=True)
        st.caption("Annualized return uses elapsed calendar time. Volatility and Sharpe use inferred periodicity (daily≈252, weekly≈52, monthly≈12). Sharpe uses the selected annual risk-free-rate assumption.")
    with tabs[2]:
        if benchmark == "None":
            st.info("Choose a benchmark series above to calculate excess return, beta, tracking error, information ratio, correlation and an annualized alpha estimate.")
        else:
            relative = benchmark_relative_metrics(prices_for_metrics, benchmark, risk_free_rate=risk_free_rate)
            if relative.empty:
                st.warning("Not enough shared observations or return variation to calculate benchmark-relative metrics.")
            else:
                st.dataframe(relative.style.format({
                    "Excess Total Return (pp)": "{:+.2f}", "Beta": "{:.2f}",
                    "Annualized Alpha Estimate (%)": "{:+.2f}%", "Tracking Error (%)": "{:.2f}%",
                    "Information Ratio": "{:.2f}", "Return Correlation": "{:.2f}",
                }, na_rep="N/A"), use_container_width=True)
                st.caption("Alpha is a simplified annualized CAPM-style estimate, not a regression forecast. Excess return is reported in percentage points. A user-selected series is not necessarily an official market benchmark.")
    with tabs[3]:
        returns = prices_for_metrics.pct_change().dropna(how="all")
        corr = returns.corr(min_periods=3)
        fig = go.Figure(go.Heatmap(z=corr.values, x=corr.columns, y=corr.index, zmin=-1, zmax=1, colorscale="RdBu", text=np.round(corr.values, 2), texttemplate="%{text}"))
        fig.update_layout(title="Correlation of periodic returns", xaxis_title="Company", yaxis_title="Company")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Correlation ranges from −1 to +1 and measures historical co-movement; it does not prove causation or guarantee diversification.")
    with tabs[4]:
        for insight in generate_insights(metrics, prices_for_metrics):
            st.markdown(f"- {insight}")
        st.markdown("#### Data coverage and cleaned closing-price matrix")
        st.dataframe(pd.DataFrame({"Valid observations": prices.notna().sum(), "Coverage (%)": (prices.notna().sum() / len(prices) * 100).round(1), "First date": prices.apply(lambda s: s.first_valid_index()), "Last date": prices.apply(lambda s: s.last_valid_index())}), use_container_width=True)
        st.dataframe(prices_for_metrics, use_container_width=True)
        st.download_button("Download comparison metrics (CSV)", metrics.to_csv().encode("utf-8"), file_name="finsight_comparison_metrics.csv", mime="text/csv")
        st.download_button("Download closing-price matrix (CSV)", prices_for_metrics.to_csv(index=True).encode("utf-8"), file_name="finsight_closing_prices.csv", mime="text/csv")
        brief = create_analytics_brief(metrics, prices_for_metrics, source_note, risk_free_rate, None if benchmark == "None" else benchmark)
        st.download_button("Download Analytics Brief (Markdown)", brief.encode("utf-8"), file_name="finsight_analytics_brief.md", mime="text/markdown", type="primary")
