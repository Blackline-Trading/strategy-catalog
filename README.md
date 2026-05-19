# strategy-catalog

Single source of truth for Blackline strategy metadata. Shared by
`tt-bot` and `trading-platform` so the same strategy type is defined
in exactly one place.

## Why this exists

Pre-package state (through 2026-05-18):
- `tt-bot/utils/config_validate.py` had a `CATALOG` dict
- `trading-platform/app/strategies.py` had a different `CATALOG` list
- Adding a strategy required updating BOTH. Drift was inevitable.
- 2026-05-19 incident: Futures Scalp + Nasdaq Short Put added to bot
  but missing from platform → every CC save 400'd silently, blocking
  the user's VPS-Day min_credit edits for hours.

This package eliminates drift by being the only place strategies are
defined.

## Adding a new strategy

1. Append an entry to `CATALOG` in `src/strategy_catalog/__init__.py`
2. Bump `__version__` (semver — pure additions are MINOR)
3. Add to the `test_known_strategies_present` expected set
4. Push to `main`
5. Pin the version in `tt-bot/requirements.txt` and
   `trading-platform/requirements.txt`
6. Deploy each repo (their tests will catch any consumer-side
   schema mismatch)

## Install

```
pip install git+https://github.com/Blackline-Trading/strategy-catalog.git@main
```

Or pin a tag:

```
pip install git+https://github.com/Blackline-Trading/strategy-catalog.git@v0.1.0
```

## Usage

```python
from strategy_catalog import (
    CATALOG,
    get_by_key, get_by_slug,
    is_known_type, get_canonical_names,
    STRATEGY_OVERLAY_FIELDS,
)

# Quick checks
is_known_type("Iron Condor")  # True
is_known_type("Strangle")     # True (alias)

# Look up
entry = get_by_key("Iron Condor")
entry["defaults"]["profit_target_pct"]  # 50

# Get all canonical names that map to one engine
get_canonical_names("Iron Condor")  # {'Iron Condor', 'Strangle'}
```
