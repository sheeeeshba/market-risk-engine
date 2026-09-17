# Security Policy

## Secrets

The repository does not require credentials for Demo mode. Never commit FRED keys, `.env`, or `.streamlit/secrets.toml`.

The Streamlit password field passes a live-mode FRED key to the in-process data adapter only. It is not written to tables, reports, the verification manifest, or download bundles.

## Reporting a vulnerability

Open a private GitHub security advisory for vulnerabilities involving credential exposure, path traversal, unsafe file handling, or dependency compromise. Do not include real API keys or sensitive portfolio data in an issue.

## Scope

This educational application is not approved for regulatory capital, production risk limits, investment advice, or live trading. Deployments that introduce real positions or shared vendor credentials require independent access control, logging, retention, and model-governance review.
