# Public Deployment Guide

The project is designed for two reviewer surfaces:

1. GitHub documents the methodology, code, tests, evidence, and limitations.
2. Streamlit Community Cloud exposes the credential-free synthetic Demo.

## Safe public configuration

The committed Demo requires no secrets. Do not publish a personal FRED key. Visitors who select live mode should supply their own key for the active session.

## Local release check

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install ".[dev]"
python -m ruff check .
python -m pytest --cov=market_risk --cov-report=term-missing
python -m streamlit run streamlit_app.py
```

Confirm that Demo opens without credentials, all seven tabs render, charts respond to the view controls, downloads contain no secrets, and the synthetic classification remains visible.

## Streamlit Community Cloud

At `https://share.streamlit.io`, select:

- repository: `sheeeeshba/market-risk-engine`;
- branch: `main`;
- entrypoint: `streamlit_app.py`;
- Python: `3.12`.

The public Demo needs no Streamlit Secrets. If a private deployment needs live mode, add `FRED_API_KEY` in the deployment settings rather than committing `.streamlit/secrets.toml`.

## Release checklist

- GitHub Actions is green on Python 3.11 and 3.12.
- The public Demo opens in a private browser window.
- `outputs/verification_manifest.json` contains successful gates.
- No `.env`, `.streamlit/secrets.toml`, cache, or local virtual environment is tracked.
- The GitHub Website field points to the deployed Streamlit URL.
- The latest dashboard screenshot is used as the repository social preview.
