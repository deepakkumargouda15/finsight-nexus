# FinSight Nexus release checklist

## Automated checks
- [x] Core analytics and ingestion tests run in the audit environment: `21 passed`.
- [x] Python syntax compilation passed during the package audit.
- [ ] Run `scripts/verify_release.ps1` in the target Python 3.12 virtual environment. It checks compilation, verifies Streamlit AppTest is installed, runs tests, and checks required release files.
- [ ] Confirm GitHub Actions passes on Python 3.12.

## Local UI checks
- [ ] Create a clean Python 3.12 virtual environment and install `requirements-dev.txt` (which includes the runtime requirements).
- [ ] Run `python -m streamlit run app.py`; the app should open in the synthetic multi-company demo by default without network access.
- [ ] Check the synthetic single-company demo: price, volume, moving averages, RSI, MACD, data quality, adjusted-close selector when available, analytics brief and CSV export.
- [ ] Upload the downloadable OHLCV template and confirm single-company charts render.
- [ ] Upload the comparison template and confirm metrics, rebased performance, drawdown, correlation, benchmark-relative metrics, insights, Analytics Brief and CSV exports render.
- [ ] Confirm risk-free-rate input changes the Sharpe ratio and benchmark alpha calculations.
- [ ] Check sparse/non-overlapping dates: the app must explain why comparable metrics are withheld.
- [ ] Upload a missing-column file and malformed file; confirm clear errors rather than a crash.
- [ ] Upload XLSX and XLS files (where available) and verify parsing.
- [ ] Try an invalid ticker and a valid ticker in live mode; provider failures must be explicit and must not replace prices with synthetic data.
- [ ] Check that no uploaded data is written to disk.

## Public release
- [ ] Push source code only; exclude `.venv`, credentials, personal data and private datasets.
- [ ] Verify all third-party packages and data rights. The offline data is generated locally; no third-party market data is bundled.
- [ ] Deploy from GitHub on Streamlit Community Cloud with `app.py` as the entry point.
- [ ] Open the public URL in an incognito browser and run the synthetic demo and upload workflow.
- [ ] Capture real UI screenshots following `SCREENSHOT_CAPTURE_GUIDE.md` and add a short demo recording. Do not use mockups as deployment evidence.
- [ ] Add the public demo URL and repository URL to the resume only after verification.

## Portfolio walkthrough evidence
- [ ] Show one successful validated upload.
- [ ] Explain return, annualized volatility, maximum drawdown and correlation in plain language.
- [ ] Demonstrate live-provider failure handling.
- [ ] State that offline series are synthetic and live data comes from Yahoo Finance via `yfinance`.


## Recruiter demo

- [ ] Rehearse `RECRUITER_WALKTHROUGH.md` in 3–4 minutes.
- [ ] Capture only real screenshots from the running app; replace local screenshots with verified public-deployment captures after publishing.
