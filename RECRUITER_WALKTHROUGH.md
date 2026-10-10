# FinSight Nexus — Recruiter Walkthrough (3–4 minutes)

## Before the demo

1. Open the deployed public URL in an incognito/private browser window.
2. Confirm the default page loads without a sign-in, local files, or a live-data request.
3. Use only synthetic or properly licensed data in a public demo. Synthetic data must remain visibly labelled fictional.

## Suggested walkthrough

### 1. Start with the business problem (20 seconds)

"FinSight Nexus is a financial analytics prototype that helps users inspect historical price data, compare securities over a shared period, and understand performance and risk metrics. It focuses on data quality and transparent assumptions, not on predicting prices."

### 2. Compare companies (45–60 seconds)

- Show the default synthetic comparison and point out the fictional-data disclosure.
- Explain rebased performance: every series starts at 100 so relative changes are easier to compare.
- Open Risk & metrics and explain total return, annualized volatility, and maximum drawdown in plain language.
- Open Correlation and explain that historical co-movement is not causation or a guarantee of diversification.

### 3. Explain a benchmark comparison (30–45 seconds)

- Choose one available series as the comparison benchmark.
- Explain excess return, beta, tracking error and information ratio.
- State that the selected series is only a user-chosen benchmark unless independently verified as an official index.

### 4. Demonstrate data quality (45 seconds)

- Switch to Upload CSV / Excel.
- Download the comparison template, upload it, and show the coverage report.
- If you have prepared a malformed test file, demonstrate that the app gives an actionable validation error instead of crashing.
- Explain that uploads are user-provided and are not verified against an exchange.

### 5. Show the business deliverable (20 seconds)

- Download the Analytics Brief.
- Point out the source disclosure, metrics, assumptions and limitations.
- Close with how a business analyst can use descriptive analytics to frame better questions, not to make unsupported predictions.

## Interview questions to prepare

- Why do the comparisons use shared dates?
- What assumptions are used to annualize volatility and Sharpe ratio?
- What does maximum drawdown communicate that total return does not?
- How can currency, dividends, corporate actions and different trading calendars bias a comparison?
- How does the application distinguish source failure from valid zero/empty data?
- What further validation would be required before using the metrics in a regulated or production financial workflow?

## Honesty rule

Do not claim the dashboard is live market data when using the synthetic demo. Do not claim that a selected series is an official benchmark unless verified. Do not present descriptive metrics as investment advice or forecasts.
