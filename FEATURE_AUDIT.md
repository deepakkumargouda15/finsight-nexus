# FinSight Nexus — Premium Build Feature Audit

Audit date: 2026-10-09
Scope: source code and test suite inside the audited release package, including the additional release-readiness updates.

## Status legend

- [x] **Implemented in code** — the feature is present in the repository.
- [~] **Partially complete / verification pending** — code/configuration exists, but a full local/browser/provider/deployment check is still required.
- [ ] **Not implemented** — not part of this build. The note says whether it is a recommended next step or intentionally out of scope.

A checked item means implemented, not necessarily proven in a real browser or with an external provider. Unit tests do not replace end-to-end testing.

## Product and user experience

- [x] Branded Streamlit dashboard with responsive wide layout, sidebar data workspace, tabs, charting and clear source disclosures.
- [x] Opens in the offline synthetic comparison demo by default; no network request is required for the default experience.
- [x] Separate data modes: live market data, CSV/Excel upload, synthetic single-company demo, synthetic comparison demo.
- [x] Explicitly identifies synthetic data as fictional and user-uploaded data as unverified.
- [x] Shows a currency comparability warning before multi-company analysis.
- [~] Browser-level usability/accessibility pass (keyboard flow, small screens, contrast and all interactions) still needs to be done locally. A manual checklist and screenshot capture guide are included.

## Data sources and ingestion

- [x] Live market data adapter using Yahoo Finance through `yfinance`.
- [x] Live requests are initiated by an explicit submit action; responses are cached.
- [x] Per-ticker failures and network/rate-limit guidance are shown; synthetic prices are not silently substituted for failed live requests.
- [x] CSV, XLSX and XLS upload support with a 20 MB application-level limit.
- [x] Single-company OHLCV upload format.
- [x] Multi-company long format (`Date,Ticker,Close`).
- [x] Multi-company wide format (`Date` plus company/series columns).
- [x] Downloadable CSV templates for single-company and comparison uploads.
- [x] Uploads are processed in memory; the app does not persist them to project files.
- [~] Successful live retrieval depends on provider/network access and has not been guaranteed by this code audit.
- [ ] Official/licensed market-data provider integration. **Recommended only if data licensing, reliability or commercial use requires it; not needed for the offline portfolio demo.**

## Data quality and provenance

- [x] Header normalization and duplicate normalized-header rejection.
- [x] Date/numeric parsing, positive price checks, OHLC consistency checks and non-finite-value handling.
- [x] Duplicate date/key handling and reporting.
- [x] Negative/missing volume reporting.
- [x] Per-company observation coverage and quality scorecard for applicable upload formats.
- [x] `DATA_PROVENANCE.md` documents live data, synthetic data, user uploads and intended use.
- [x] No third-party market-price CSV is bundled; demo series are generated locally and fictional.
- [~] The quality score is a structural heuristic, not an audit/certification of data accuracy; this is disclosed in the UI.
- [ ] Automatic currency conversion, corporate-action reconciliation, exchange-calendar normalization and external price verification. **Not implemented; users are warned not to assume these operations happen automatically.**

## Single-company analysis

- [x] Closing-price chart and moving averages.
- [x] Volume chart.
- [x] RSI and MACD indicators.
- [x] Total return, annualized return, annualized volatility, maximum drawdown, best/worst period and Sharpe ratio.
- [x] Configurable annual risk-free-rate assumption.
- [x] Optional Close / Adjusted Close basis selection when adjusted prices exist.
- [x] Data-quality display and cleaned CSV export.
- [x] Short-history warning for unstable annualized estimates.

## Multi-company analytics

- [x] Rebased performance comparison and drawdown chart.
- [x] Shared-date comparison logic with a clear minimum-history warning.
- [x] Comparative return/risk metric table.
- [x] Return-correlation heatmap and coverage display.
- [x] User-selectable series benchmark.
- [x] Benchmark-relative excess total return, beta, tracking error, information ratio, correlation and simplified annualized alpha estimate.
- [x] Documentation identifies alpha as a simplified CAPM-style estimate, not a regression forecast.
- [x] Descriptive insight generation from calculated metrics.
- [x] CSV exports for metrics and price matrix.

## Reporting and documentation

- [x] Downloadable Markdown Analytics Brief.
- [x] Report includes data source, analysis window, metrics, benchmark-relative results when selected, methodology and limitations.
- [x] README includes setup instructions, accepted upload formats, metric definitions, test instructions and deployment steps.
- [x] Deployment checklist and GitHub Actions workflow are present.
- [x] Release verification script, recruiter walkthrough, screenshot capture guide, and release-status register are included.
- [~] README and code have been reviewed for consistency; the comparison CSV template was expanded to four dates because the dashboard requires at least four shared observations.
- [ ] Final screenshots and a demo recording captured from the real running app; exact instructions and filenames are in `SCREENSHOT_CAPTURE_GUIDE.md`.

## Automated verification

- [x] Core analytics, ingestion and robustness tests: **21 passed** in the available audit environment.
- [x] Python syntax compilation passed after the audit fixes.
- [x] CI workflow configuration exists for Python 3.12 and installs the development requirements, explicitly verifies AppTest availability, runs the complete test suite, and compiles the project.
- [~] Four Streamlit `AppTest` smoke tests are included for default comparison, single-company demo, upload mode, and live mode before submission. They could not be executed in this audit environment because Streamlit is not installed here. The CI workflow now explicitly checks that Streamlit AppTest is importable so these tests cannot silently skip in CI.
- [ ] Full browser/end-to-end verification of all modes and download interactions.
- [ ] Confirm GitHub Actions passes on the actual published repository.

## Deployment and production-like features

- [x] Streamlit Community Cloud deployment instructions are included.
- [x] `.gitignore` excludes virtual environments, caches, secrets and common private upload files.
- [~] Project is deployment-configured but not published or externally verified.
- [ ] Public Streamlit Community Cloud URL.
- [ ] Public GitHub repository URL and CI run evidence.
- [ ] Incognito-browser test of the deployed URL.
- [ ] Persistent database, authentication, user workspaces or saved analyses. **Intentionally not included in this single-user/session-based portfolio prototype; add only if the product requirement changes.**

## Audit actions completed in this revision

- [x] Expanded the comparison CSV template to provide four shared dates, matching the dashboard's minimum-history rule.
- [x] Added a visible multi-currency comparability warning to comparison analytics.
- [x] Corrected the in-app methodology text so it reflects the configurable risk-free-rate assumption rather than claiming the rate is always zero.
- [x] Clarified in the README that passing unit tests does not establish full browser or live-provider success.
- [x] Removed generated Python bytecode and pytest cache files from the distributable ZIP.
- [x] Added AppTest coverage for the upload empty state and live form before submit.
- [x] Changed the test workflow to fail early if Streamlit AppTest is unavailable rather than silently treating UI tests as optional.
- [x] Added a Windows release-verification script, a timed recruiter walkthrough, and a screenshot capture guide.

## Release decision

**Status: feature-complete portfolio prototype; not yet release-verified.** The main analytics and data-handling capabilities are implemented. The remaining blockers for claiming a fully working recruiter demo are local Streamlit AppTest/browser verification, a successful CI run, and an actual public deployment check. Live provider availability and data licensing must remain explicit limitations.
