"""Allow ``python -m market_risk`` to use the production CLI."""

from .cli import main

raise SystemExit(main())
