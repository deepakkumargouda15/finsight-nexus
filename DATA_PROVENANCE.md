# Data provenance and licensing

## Live market data
- Live requests use Yahoo Finance through the community `yfinance` Python package. This is not an official LSEG data feed. Provider availability, latency, completeness, permitted uses and redistribution rights are not guaranteed by this project. Review the applicable provider terms before any commercial use.
- The application requests data only after the user submits the live-data form. It caches successful and unsuccessful results temporarily and surfaces provider failures rather than silently substituting other data.

## Offline demonstration data
- The single-company OHLCV and multi-company price series are generated locally using deterministic random seeds. Company names are fictional. These series are for testing charts and calculations only and must never be described as real historical prices.
- No third-party historical market dataset is bundled with this version.

## User uploads
- Uploaded CSV/XLS/XLSX data is supplied by the user and processed in memory during the active app session. The app validates schema and basic numerical consistency but does not authenticate data source, ownership, license or accuracy. Users are responsible for ensuring they have the right to upload and analyze their files.

## Intended use
FinSight Nexus is an independent educational portfolio project. It is not an LSEG product, a regulated financial service, or investment advice. Historical metrics are descriptive and do not predict future performance.
