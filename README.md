# FinSight Nexus — Financial Market Intelligence & Analytics

A Streamlit portfolio project demonstrating financial data ingestion, data quality checks, comparative performance analysis, risk metrics, and explainable descriptive insights. The app opens in an offline synthetic comparison demo by default, so recruiters can explore it without a market-data connection.

> **Important:** This is an independent portfolio project, not an LSEG product and not investment advice. Historical performance is not a forecast.

## Features

- **Multiple data sources:** Yahoo Finance via `yfinance`, synthetic single-company OHLCV demo, user-uploaded CSV/Excel, and an explicitly synthetic offline comparison demo.
- **Data validation:** required-column checks, date and numeric parsing, positive OHLC price validation, OHLC consistency checks, duplicate normalized-header rejection, invalid-row removal, duplicate-date handling, volume anomaly reporting, and a quality scorecard.
- **Single-company analysis:** closing-price history, moving averages, volume, RSI, MACD, returns, volatility, and drawdown.
- **Multi-company comparison:** common-date comparison, rebased performance and drawdown charts, total/annualized returns, annualized volatility, maximum drawdown, best/worst period, configurable annual risk-free-rate assumption for Sharpe ratio, and return-correlation heatmap.
- **Benchmark-relative analysis:** optional user-selected series benchmark with excess total return, beta, tracking error, information ratio, return correlation, and a simplified annualized alpha estimate. A selected series is not automatically an official market index.
- **Analytics Brief:** downloadable Markdown report containing the period, source disclosure, calculated highlights, metrics, benchmark-relative results, methodology and caveats.
- **Adjusted-close support:** when an uploaded/provider dataset includes both `Close` and `Adj Close`, users can choose which series drives the price and technical-indicator views; the raw columns remain visible in the data tab.
- **Data quality scorecard:** quality estimate, invalid/duplicate counts, volume anomalies and per-company coverage where available.
- **Business insights:** automatically generated descriptive observations tied to calculated metrics, with limitations displayed in the app.
- **Exports:** download cleaned price data, comparison metrics, comparison price matrix, and synthetic demo data.
- **Transparent provider failures:** live-data errors are surfaced; synthetic demo prices are never silently substituted for a requested live ticker.

## Run locally (Windows PowerShell)

Use Python 3.12. From the project root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, normally `http://localhost:8501`.

## Data formats

### Single company (CSV/XLSX)

Required columns: `Date`, `Open`, `High`, `Low`, `Close`. `Volume` is optional.

```csv
Date,Open,High,Low,Close,Volume
2025-01-01,100,105,98,103,12000
2025-01-02,103,108,101,106,15000
```

### Multi-company long format

```csv
Date,Ticker,Close
2025-01-01,AAA,100
2025-01-01,BBB,50
2025-01-02,AAA,102
2025-01-02,BBB,49
```

At least two distinct tickers are required.

### Multi-company wide format

```csv
Date,DEMO_ALPHA,DEMO_BETA,DEMO_GAMMA
2025-01-01,100,50,80
2025-01-02,102,49,82
```

Use actual closing prices from a source you are entitled to use. The dashboard does not validate uploaded prices against an exchange.

## Live data notes

Market data is requested from Yahoo Finance through `yfinance` only after the user submits the form. Requests may fail due to network conditions, provider changes, rate limiting, ticker coverage or missing observations, and data is not guaranteed to be real-time. Use the retry/cache-clear control sparingly. If the provider is unavailable, use either fictional offline demo or upload your own dataset. Synthetic prices are not actual market data.

## Tests

Run:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover upload validation, CSV/XLSX ingestion, data-quality edge cases, synthetic demo generation, risk-free-rate handling, benchmark-relative calculations, report generation, and Streamlit AppTest smoke checks for default, single-company, upload-empty, and live-form pre-submit paths. The UI smoke tests require Streamlit to be installed; a passing unit-test run alone does not prove every browser interaction or live-provider request works. Also manually test the Streamlit UI with: a valid OHLCV CSV, an invalid/missing-column file, long-form multi-company data, wide-form multi-company data, both offline demos, and live provider failure.

## Deployment on Streamlit Community Cloud

1. Create a GitHub repository and push the project files (do not upload `.venv`, secrets, or personal data).
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and create an app from the repository.
3. Select the intended branch and `app.py` as the entrypoint.
4. Choose Python 3.12 in advanced settings if prompted; deployment installs the dependencies from `requirements.txt`.
5. Wait for the build, then test every data mode using the public URL.
6. Document any live-provider limitations on the repository page.

See [`RECRUITER_WALKTHROUGH.md`](RECRUITER_WALKTHROUGH.md), [`SCREENSHOT_CAPTURE_GUIDE.md`](SCREENSHOT_CAPTURE_GUIDE.md), and [`RELEASE_STATUS.md`](RELEASE_STATUS.md) for the demo narrative, evidence-capture plan, and release gates. Run `scripts/verify_release.ps1` on Windows before deployment.

No API keys are required by this project. If credentials are added in a future version, store them in Streamlit Secrets or environment variables; never commit secrets to GitHub. Streamlit Community Cloud ephemeral local storage is not a durable database, and uploaded data is not persisted by this app.

## Methodology and caveats

- Total return = final close / initial close − 1.
- Annualized volatility uses sample standard deviation of periodic returns multiplied by the square root of inferred periods per year.
- Maximum drawdown measures the largest peak-to-trough percentage decline.
- Sharpe ratio uses a user-selected annual risk-free-rate assumption, converted to an inferred periodic rate; zero is only the default.
- Correlation describes historical co-movement, not causation.
- Benchmark-relative alpha is a simplified annualized CAPM-style estimate, not a regression forecast.
- Different currencies, dividend adjustments, corporate actions, exchange calendars, stale data and non-overlapping date ranges can distort comparisons. Review data coverage before drawing conclusions.

## Data provenance and licensing

See [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md) before public deployment. Offline demonstration data is generated locally and uses fictional names; no third-party market-price CSV is bundled.
