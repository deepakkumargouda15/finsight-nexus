from __future__ import annotations
import streamlit as st
from src.analytics import make_synthetic_comparison
from src.data import get_synthetic_stock_data, get_multi_stock_data
from src.helpers import compute_indicators
from src.ingestion import load_upload
from src.ui import render_single_company, render_comparison, render_quality_report

st.set_page_config(page_title="FinSight Nexus | Financial Intelligence", page_icon="📈", layout="wide")

st.markdown("""
<style>
:root { --fs-accent: #3b82f6; }
.block-container { padding-top: 1.6rem; padding-bottom: 2rem; max-width: 1500px; }
.hero { padding: 1.4rem 1.6rem; border-radius: 18px; background: linear-gradient(120deg, rgba(30,64,175,.16), rgba(14,165,233,.06)); border: 1px solid rgba(100,116,139,.25); margin-bottom: 1.2rem; }
.hero h1 { margin: 0 0 .25rem 0; letter-spacing: -.04em; }
.hero p { margin: 0; color: #64748b; font-size: 1.02rem; }
[data-testid="stMetric"] { border: 1px solid rgba(100,116,139,.2); padding: .75rem; border-radius: 12px; }
</style>
<div class="hero">
  <h1>📈 FinSight Nexus</h1>
  <p>Financial market intelligence · performance analytics · risk insights</p>
</div>
""", unsafe_allow_html=True)

st.markdown("Explore market data, validate your own dataset, compare companies on a consistent basis, and turn historical prices into transparent analytical insights.")

with st.sidebar:
    st.markdown("## Data workspace")
    data_mode = st.radio(
        "Choose a data source",
        [
            "Live market data",
            "Upload CSV / Excel",
            "Synthetic single-company demo",
            "Synthetic comparison demo",
        ],
        index=3,
        help="The default view is a fictional offline demo so the dashboard opens with charts even if no live-data provider is available.",
    )
    st.divider()
    st.caption("FinSight Nexus is a portfolio demonstration, not an LSEG product or investment-advice service.")

if data_mode == "Live market data":
    st.subheader("Live market data")
    st.caption("Requests are made only when you submit the form. Yahoo Finance via yfinance is a best-effort public data source and may rate-limit or fail.")
    with st.sidebar.form("live_market_form"):
        primary_ticker = st.text_input("Primary ticker", value="AAPL", help="Examples: AAPL, MSFT, GOOGL, RELIANCE.NS, TCS.NS").strip().upper()
        compare_input = st.text_input("Additional tickers (comma-separated)", value="MSFT, GOOGL", help="Enter up to three additional symbols; leave blank for a single-company view.")
        period = st.selectbox("History window", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2, format_func=lambda x: {"1mo":"1 month", "3mo":"3 months", "6mo":"6 months", "1y":"1 year", "2y":"2 years", "5y":"5 years"}[x])
        interval = st.selectbox("Observation interval", ["1d", "1wk", "1mo"], index=0, format_func=lambda x: {"1d":"Daily", "1wk":"Weekly", "1mo":"Monthly"}[x])
        submitted = st.form_submit_button("Fetch market data", type="primary", use_container_width=True)
    if submitted:
        extra = [x.strip().upper() for x in compare_input.split(",") if x.strip()]
        all_symbols = list(dict.fromkeys(([primary_ticker] if primary_ticker else []) + extra))
        if len(all_symbols) > 4:
            st.warning("To reduce provider throttling, this demo fetches at most four tickers per request. Only the first four unique symbols will be used.")
        symbols = all_symbols[:4]
        if not symbols:
            st.session_state.pop("live_request", None)
            st.error("Enter at least one ticker symbol.")
        else:
            st.session_state["live_request"] = {"tickers": symbols, "primary": primary_ticker or symbols[0], "period": period, "interval": interval}
    request = st.session_state.get("live_request")
    if not request:
        st.info("Enter one or more tickers in the sidebar and select **Fetch market data** to start. If the provider is unavailable, try the synthetic demo or upload your own dataset.")
    else:
        if st.button("Retry / clear cached provider responses"):
            st.cache_data.clear()
            st.rerun()
        with st.spinner(f"Requesting data for {', '.join(request['tickers'])}…"):
            closes, failures = get_multi_stock_data(tuple(request["tickers"]), request["period"], request["interval"])
        if failures:
            with st.expander(f"Provider status: {len(failures)} ticker(s) unavailable", expanded=closes.empty):
                for symbol, reason in failures.items():
                    st.warning(f"**{symbol}:** {reason}")
        if closes.empty:
            st.error("No usable live prices were returned. This is a provider/network limitation, not evidence that the entire dashboard is broken.")
            st.markdown("**Next steps:** verify the ticker, wait before retrying if rate-limited, or switch to *Synthetic single-company demo* / *Upload CSV / Excel*. Synthetic demo data will never be substituted silently for a live ticker.")
        else:
            st.success(f"Retrieved {closes.shape[1]} of {len(request['tickers'])} requested ticker(s). Source: Yahoo Finance via yfinance. Latest provider data may be delayed and is not guaranteed to be real-time.")
            if closes.shape[1] >= 2:
                render_comparison(closes, "Company performance comparison", f"Yahoo Finance · {request['period']} · {request['interval']}. Comparison uses shared dates when available.")
            primary = request["primary"]
            if primary in closes.columns:
                primary_df = closes[[primary]].rename(columns={primary: "Close"}).copy()
                # Single-stock charts need OHLC. Retrieve cached primary OHLC from the same provider adapter.
                from src.data import get_stock_data
                full_df, info = get_stock_data(primary, request["period"], request["interval"])
                if not full_df.empty:
                    full_df = compute_indicators(full_df)
                    st.divider()
                    render_single_company(full_df, info, primary)
                else:
                    st.info(f"Price series for {primary} is available for comparison, but full OHLC data was not returned for the single-company charts.")
            elif closes.shape[1] == 1:
                symbol = closes.columns[0]
                st.info(f"The primary ticker was unavailable; showing comparison data for {symbol}.")

elif data_mode == "Upload CSV / Excel":
    st.subheader("Bring your own market data")
    st.markdown("Upload either **single-company OHLCV** data or **multi-company closing prices**. The app validates and previews the data before calculating metrics.")
    uploaded_file = st.file_uploader(
        "Choose a CSV, XLSX, or XLS file",
        type=["csv", "xlsx", "xls"],
        help="Maximum file size: 20 MB. Single-company format: Date, Open, High, Low, Close, optional Volume. Comparison format: Date + Ticker + Close, or Date + one close-price column per company.",
    )
    template_col1, template_col2 = st.columns(2)
    with template_col1:
        ohlcv_template = "Date,Open,High,Low,Close,Volume\n2025-01-01,100,105,98,103,12000\n2025-01-02,103,108,101,106,15000\n2025-01-03,106,110,104,109,18000\n"
        st.download_button("Download OHLCV template", ohlcv_template, file_name="finsight_ohlcv_template.csv", mime="text/csv")
    with template_col2:
        comparison_template = "Date,Ticker,Close\n2025-01-01,AAA,100\n2025-01-01,BBB,50\n2025-01-02,AAA,102\n2025-01-02,BBB,51\n2025-01-03,AAA,101\n2025-01-03,BBB,52\n2025-01-06,AAA,104\n2025-01-06,BBB,53\n"
        st.download_button("Download comparison template", comparison_template, file_name="finsight_comparison_template.csv", mime="text/csv")
    with st.expander("See accepted formats and sample templates"):
        st.markdown("**Single company — OHLCV**")
        st.code("Date,Open,High,Low,Close,Volume\n2025-01-01,100,105,98,103,12000\n2025-01-02,103,108,101,106,15000", language="csv")
        st.markdown("**Multiple companies — long format**")
        st.code("Date,Ticker,Close\n2025-01-01,AAA,100\n2025-01-01,BBB,50\n2025-01-02,AAA,102\n2025-01-02,BBB,49\n2025-01-03,AAA,101\n2025-01-03,BBB,51\n2025-01-06,AAA,104\n2025-01-06,BBB,52", language="csv")
        st.markdown("**Multiple companies — wide format**")
        st.code("Date,DEMO_ALPHA,DEMO_BETA,DEMO_GAMMA\n2025-01-01,100,50,80\n2025-01-02,102,49,82", language="csv")
    if uploaded_file is None:
        st.info("Choose a file to begin. Uploaded files are processed in memory for this session; they are not written into the project folder.")
    else:
        kind, frame, report, message = load_upload(uploaded_file)
        if kind == "error":
            st.error(message)
            st.markdown("Check the column names and values using one of the templates above, then upload again.")
        else:
            st.success(message)
            st.caption(f"Source: user-uploaded file `{uploaded_file.name}`. These prices are user-provided and are not independently verified as market data.")
            if kind == "single":
                info = {
                    "shortName": uploaded_file.name, "longName": uploaded_file.name,
                    "data_source": f"User upload: {uploaded_file.name}", "is_upload": True,
                    "quality_report": report,
                }
                from src.helpers import compute_indicators
                render_single_company(compute_indicators(frame), info, uploaded_file.name)
            else:
                render_quality_report(report)
                render_comparison(frame, "Uploaded multi-company comparison", "User-provided closing prices · no external verification performed.")

elif data_mode == "Synthetic single-company demo":
    st.subheader("Synthetic single-company demo")
    try:
        frame, info = get_synthetic_stock_data()
        st.warning("**Fictional demonstration data:** this OHLCV series is generated locally. It is not a real company, security, or market-price history.")
        from src.helpers import compute_indicators
        render_single_company(compute_indicators(frame), info, "DEMO_COMPANY — synthetic data")
        st.download_button("Download synthetic OHLCV data (CSV)", frame.to_csv(index=True).encode("utf-8"), file_name="finsight_synthetic_ohlcv.csv", mime="text/csv")
    except Exception as exc:
        st.error(f"Could not generate synthetic demonstration data: {exc}")

else:
    st.subheader("Offline multi-company comparison demo")
    st.warning("All series below are **synthetic and fictional**. They are generated to demonstrate analytics and UI behavior; they are not real securities or historical market prices.")
    demo = make_synthetic_comparison()
    render_comparison(demo, "Synthetic company performance and risk", "Generated locally · deterministic seed · fictional symbols · for demonstration only.")
    st.download_button("Download synthetic demo data (CSV)", demo.to_csv(index=True).encode("utf-8"), file_name="finsight_synthetic_demo_prices.csv", mime="text/csv")

st.divider()
with st.expander("Methodology, data sources & limitations"):
    st.markdown("""
**Data sources**
- Live mode: Yahoo Finance accessed through the community `yfinance` Python package. Availability, completeness, latency and rate limits are not guaranteed.
- Synthetic single-company demo: generated locally with fictional OHLCV prices; it is not a real company or market history.
- Upload mode: data supplied by the user. The application validates structure and basic price consistency but does not verify provenance or correctness against an exchange.
- Synthetic comparison demo: generated fictional price series, clearly labelled as synthetic.

**Metric definitions**
- Total return: ending close divided by starting close, minus one.
- Annualized volatility: standard deviation of periodic returns multiplied by the square root of the inferred number of periods per year.
- Maximum drawdown: largest percentage decline from a previous running peak.
- Sharpe ratio: mean periodic excess return divided by periodic return standard deviation and annualized, using the user-selected annual risk-free-rate assumption (zero by default).
- Correlation: historical linear co-movement of periodic returns; it does not imply causation.

**Limitations**
- The dashboard is an educational portfolio project, not an official LSEG product, regulated financial service, or investment recommendation.
- Corporate actions, survivorship bias, stale observations, exchange calendars, currencies, dividends and different market closing times can affect comparisons.
- Metrics are only as reliable as the underlying data and chosen date range. Historical performance does not predict future performance.
- Uploaded files are handled in memory for the current app session; persistence and multi-user account storage are not implemented.
""")
st.caption("Built as a financial analytics portfolio prototype. Verify all data and assumptions before using results for any consequential decision.")
