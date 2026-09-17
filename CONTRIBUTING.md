# Contributing

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install ".[dev]"
```

## Quality gates

```bash
python -m ruff check .
python -m pytest --cov=market_risk --cov-report=term-missing
```

Keep financial conventions explicit, preserve the positive-loss VaR/ES sign convention, and add tests at the public module interface for every behaviour change. Generated synthetic outputs must retain their watermark.

Never commit credentials, `.env`, `.streamlit/secrets.toml`, virtual environments, caches, or unlicensed market data.
