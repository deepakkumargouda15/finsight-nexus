# User-uploaded data guide

Choose **Upload CSV / Excel** in the sidebar. Uploads are processed in memory and are not persisted to a database. The app accepts CSV, XLSX and XLS files up to 20 MB.

## Single-company OHLCV
Required columns (case-insensitive): `Date`, `Open`, `High`, `Low`, `Close`. `Volume` is optional and defaults to zero. Common aliases such as `datetime`, `timestamp`, `adj close` and `vol` are supported.

```csv
Date,Open,High,Low,Close,Volume
2025-01-01,100,105,98,103,12000
2025-01-02,103,108,101,106,15000
2025-01-03,106,110,104,109,18000
```

## Multi-company long format

```csv
Date,Ticker,Close
2025-01-01,AAA,100
2025-01-01,BBB,50
2025-01-02,AAA,102
2025-01-02,BBB,51
2025-01-03,AAA,101
2025-01-03,BBB,52
```

At least two tickers and three usable dates are needed for the comparison charts.

## Multi-company wide format

```csv
Date,DEMO_ALPHA,DEMO_BETA,DEMO_GAMMA
2025-01-01,100,50,80
2025-01-02,102,49,82
2025-01-03,242,422,193
```

## Validation behavior
- Date values are parsed and invalid dates are removed.
- OHLC prices must be positive and satisfy `High >= Open/Close/Low` and `Low <= Open/Close/High`.
- Non-numeric/non-finite values are rejected or treated as missing. Negative volume is clipped to zero.
- Duplicate dates (single-company) or duplicate ticker/date pairs (long comparison) keep the last row.
- Uploaded prices are not checked against exchange records.

Use the template-download buttons in the app to create compatible starter files.
