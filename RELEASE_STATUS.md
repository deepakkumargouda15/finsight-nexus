# Release status — FinSight Nexus

## Completed in source/package

- [x] Four data modes: live provider, CSV/Excel upload, synthetic single-company demo, synthetic multi-company demo.
- [x] Data validation and quality summaries.
- [x] Comparative performance, risk metrics, benchmark-relative metrics, correlation and descriptive insights.
- [x] Downloadable Analytics Brief and CSV exports.
- [x] Source-data disclosures and methodology/limitations text.
- [x] Unit tests for ingestion and analytics.
- [x] Streamlit AppTest smoke tests for default, synthetic single-company, upload-empty state, and live form pre-submit state.
- [x] CI workflow installs the complete development requirements, runs pytest, and compiles the code.
- [x] Release verification script and recruiter walkthrough.

## Must be completed before calling it release-ready

- [ ] Run `scripts/verify_release.ps1` on the target Windows/Python 3.12 environment; all tests should pass and UI tests should not be skipped.
- [ ] Launch Streamlit and manually test the checklist in `DEPLOYMENT_CHECKLIST.md`.
- [ ] Publish repository to the user's GitHub account and verify the GitHub Actions run is green.
- [ ] Deploy from that repository to Streamlit Community Cloud.
- [ ] Test the public URL in an incognito browser (default demo, upload, download, responsive layout).
- [ ] Capture real screenshots using `SCREENSHOT_CAPTURE_GUIDE.md` and save them under `docs/screenshots/`.
- [ ] Record or rehearse the flow in `RECRUITER_WALKTHROUGH.md`.
- [ ] Only after public verification, add repository and demo URLs to the resume.

## Not included by design (optional production features)

Authentication, persistent user workspaces/database, licensed enterprise market-data provider, and automatic currency/exchange-calendar normalization are outside this portfolio prototype's current scope.
