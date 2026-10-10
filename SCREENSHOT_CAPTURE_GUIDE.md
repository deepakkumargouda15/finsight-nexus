# Screenshot capture guide

Screenshots must be captured from the **actual running application** after the final local tests pass. Do not use mockups as evidence of a deployed UI.

Save the following images under `docs/screenshots/` (create the folder first):

1. `01-overview.png` — default synthetic comparison, showing the fictional-data disclosure and rebased performance chart.
2. `02-risk-metrics.png` — Risk & metrics tab with the metrics table visible.
3. `03-benchmark-analysis.png` — benchmark selector and relative metrics table.
4. `04-data-quality-upload.png` — uploaded comparison dataset and quality/coverage report.
5. `05-analytics-brief.png` — Insights & report tab with the Analytics Brief download button.
6. `06-provider-failure.png` — only if a live request fails naturally; show the explicit failure message and no synthetic substitution.

## Windows steps

1. Run `python -m streamlit run app.py` and open the local URL.
2. Resize the browser to a consistent desktop size (for example 1440 × 900) and zoom to 100%.
3. Navigate to each state listed above.
4. Press `Win + Shift + S`, select the application content, and save the PNG using the exact filename.
5. Check that no personal data, credentials, browser profile information or private files are visible.
6. After deployment, repeat the overview and upload screenshots using the public URL and replace local screenshots with those verified public-demo captures.

Never create or label a screenshot as "deployed" unless it was captured from the public deployment.
