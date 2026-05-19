"""Blackline Strategy Catalog — single source of truth for strategy metadata.

This package is the ONE place where strategy types are defined. Both
tt-bot (bot.py + utils/config_validate.py) and trading-platform
(app/strategies.py + app/config_validate.py) import from here so a
new strategy lives in exactly one file.

Previously the two repos each maintained their own CATALOG. Drift
between them caused user-visible bugs (2026-05-19: Futures Scalp +
Nasdaq Short Put added to bot but missing from platform → every CC
save 400'd silently, blocking the user's VPS-Day min_credit edits).

Adding a new strategy:
  1. Append a new dict to `CATALOG` below
  2. Bump `__version__` (semver — additions are MINOR)
  3. Push to main
  4. Both repos pull the new version on their next deploy
"""
from __future__ import annotations

__version__ = "0.1.0"


# Each catalog entry is a dict with these required keys:
#   key         — display key (matches BotConfig strategy["type"] strings)
#   name        — user-facing display name
#   slug        — snake_case identifier used in URLs, CSV exports, filter UIs
#   aliases     — alternative names that map to this same strategy
#                  (legacy spellings, variant names like Day/Swing if they
#                  share the same engine config-shape)
#   description — short user-facing summary (1-2 sentences)
#   risk        — risk profile callout for UX
#   defaults    — keys consumed by UserStrategySettings JSON overrides
#                  (profit_target_pct, stop_loss_mult, max_positions,
#                  max_contracts, max_bp_pct, avoid_earnings, avoid_fomc).
#                  Strategy-specific knobs (drop_pct_threshold for NSP,
#                  l1_trigger_drop for FSCALP, etc.) live in the bot's
#                  engine config dataclass, NOT here. This catalog is for
#                  the cross-strategy overlay set.
CATALOG: list[dict] = [
    {
        "key": "Iron Condor",
        "name": "Iron Condor",
        "slug": "iron_condor",
        "aliases": ["Strangle"],
        "description": "Sell an OTM call spread and put spread simultaneously on the same underlying and expiration. Profits when the underlying stays within a range.",
        "risk": "Defined risk. Max loss = wing width − credit received.",
        "defaults": {"profit_target_pct": 50, "stop_loss_mult": 2, "max_positions": 3, "max_contracts": 5, "max_bp_pct": 5, "avoid_earnings": True, "avoid_fomc": True},
    },
    {
        "key": "Vertical Spread",
        "name": "Vertical Put Spread",
        "slug": "vps",
        "aliases": ["Vertical Put Spread"],
        "description": "Sell an OTM put and buy a further OTM put on the same expiration. Bullish-to-neutral credit strategy.",
        "risk": "Defined risk. Max loss = wing width − credit received.",
        "defaults": {"profit_target_pct": 50, "stop_loss_mult": 2, "max_positions": 3, "max_contracts": 5, "max_bp_pct": 5, "avoid_earnings": False, "avoid_fomc": False},
    },
    {
        "key": "Covered Call Wheel",
        "name": "Covered Call Wheel",
        "slug": "wheel",
        "aliases": [],
        "description": "Sell cash-secured puts until assigned, then sell covered calls until called away. Repeats indefinitely to collect premium.",
        "risk": "Substantial downside risk if underlying drops sharply after assignment.",
        "defaults": {"profit_target_pct": 50, "stop_loss_mult": 2, "max_positions": 3, "max_contracts": 5, "max_bp_pct": 10, "avoid_earnings": True, "avoid_fomc": True},
    },
    {
        "key": "Zero DTE",
        "name": "0 DTE Credit Spreads",
        "slug": "zero_dte",
        "aliases": ["0 DTE"],
        "description": "Same-day expiration credit spreads on SPX. High theta decay, typically entered in the morning and closed by end of day.",
        "risk": "Defined risk. Fast-moving intraday positions require active monitoring.",
        "defaults": {"profit_target_pct": 50, "stop_loss_mult": 2, "max_positions": 1, "max_contracts": 1, "max_bp_pct": 10, "avoid_earnings": False, "avoid_fomc": False},
    },
    {
        "key": "Liquidity Raid",
        "name": "Liquidity Raid",
        "slug": "liquidity_raid",
        "aliases": [],
        "description": "Trades options when price sweeps liquidity zones (stop hunts). Uses EMA trend, RSI, and VWAP filters.",
        "risk": "Defined risk (spreads). Requires strong directional move to trigger.",
        "defaults": {"profit_target_pct": 100, "stop_loss_mult": 2, "max_positions": 2, "max_contracts": 2, "max_bp_pct": 2, "avoid_earnings": False, "avoid_fomc": False},
    },
    {
        "key": "Momentum Breakout",
        "name": "Momentum Breakout",
        "slug": "momentum_breakout",
        "aliases": [],
        "description": "Buys call or put debit spreads when a stock breaks out of a Bollinger Band squeeze on high relative volume.",
        "risk": "Defined risk (debit spread). Loses full premium if breakout fails.",
        "defaults": {"profit_target_pct": 75, "stop_loss_mult": 2, "max_positions": 5, "max_contracts": 3, "max_bp_pct": 3, "avoid_earnings": True, "avoid_fomc": True},
    },
    {
        "key": "Supply Demand",
        "name": "Supply & Demand",
        "slug": "supply_demand",
        "aliases": ["Supply & Demand"],
        "description": "Trades options at high-grade supply and demand zones identified on higher timeframes. Uses EMA trend and Stochastic RSI filters.",
        "risk": "Defined risk (spreads). Zone quality degrades if market structure changes.",
        "defaults": {"profit_target_pct": 75, "stop_loss_mult": 2, "max_positions": 5, "max_contracts": 3, "max_bp_pct": 3, "avoid_earnings": True, "avoid_fomc": True},
    },
    {
        "key": "Futures Scalp",
        "name": "Futures Scalp",
        "slug": "futures_scalp",
        # Aliases cover the variant names that share this engine
        # (Nasdaq Day Trade trades /NQM6, S&P Day Trade trades /ESM6,
        # both use FuturesScalpConfig).
        "aliases": ["Nasdaq Day Trade", "S&P Day Trade"],
        "description": "Rolling-extreme scalp on futures contracts (/NQ /MNQ /ES /MES). L1/L2 long on pullback from session high; L3 short on breakout from session low. GTC limit at profit target; bot-monitored stop loss.",
        "risk": "Direct futures exposure. Stop losses are bot-monitored; missed cycle could leave the position open past the stop.",
        "defaults": {"profit_target_pct": 50, "stop_loss_mult": 1, "max_positions": 3, "max_contracts": 1, "max_bp_pct": 5, "avoid_earnings": False, "avoid_fomc": False},
    },
    {
        "key": "Nasdaq Short Put",
        "name": "Nasdaq Short Put",
        "slug": "nasdaq_short_put",
        "aliases": [],
        "description": "Sell a naked short put for credit on /NQ /MNQ /ES /MES futures when the underlying drops X% from the prior session close. Delta-targeted strike, 45 DTE monthly cycle.",
        "risk": "Naked short put — assignment exposure at strike. Stop loss at 2× credit caps the loss leg.",
        "defaults": {"profit_target_pct": 50, "stop_loss_mult": 2, "max_positions": 4, "max_contracts": 1, "max_bp_pct": 10, "avoid_earnings": False, "avoid_fomc": False},
    },
]

# ── Derived lookups (no mutation past module load) ───────────────────────────

CATALOG_BY_KEY: dict[str, dict] = {s["key"]: s for s in CATALOG}
CATALOG_BY_SLUG: dict[str, dict] = {s["slug"]: s for s in CATALOG}

# Canonical-names-by-key: every name (primary + aliases) that maps to this
# strategy's engine. Used by the platform's config_validate for the #48
# type/name desync check.
CANONICAL_NAMES_BY_KEY: dict[str, set[str]] = {}
for _s in CATALOG:
    _names = {_s["key"]}
    for _alias in _s["aliases"]:
        _names.add(_alias)
    # Convention: the "name" field (user-facing) is also accepted when
    # different from the key (e.g. Vertical Spread → "Vertical Put Spread").
    if _s["name"] != _s["key"]:
        _names.add(_s["name"])
    CANONICAL_NAMES_BY_KEY[_s["key"]] = _names

ALL_CANONICAL_NAMES: set[str] = {
    n for names in CANONICAL_NAMES_BY_KEY.values() for n in names
}

# Forward + reverse aliases. e.g. "Strangle" → CANONICAL_NAMES_BY_KEY["Iron Condor"].
# Used by validator to accept legacy spellings.
CANONICAL_NAMES_BY_TYPE: dict[str, set[str]] = dict(CANONICAL_NAMES_BY_KEY)
for _s in CATALOG:
    for _alias in _s["aliases"]:
        CANONICAL_NAMES_BY_TYPE[_alias] = CANONICAL_NAMES_BY_KEY[_s["key"]]

# Single source of truth for the per-strategy "overlay" field set.
# These are the fields:
#   - appearing in CATALOG[*].defaults
#   - existing as columns on UserStrategySettings (per-user overrides)
#   - existing as columns on PlatformStrategyDefaults (admin-set defaults)
#   - copied from row → bot strategy block in bot_api._apply_user_overlay
# Adding a new overlay field: extend this tuple + run migrations.
STRATEGY_OVERLAY_FIELDS: tuple[str, ...] = (
    "profit_target_pct",
    "stop_loss_mult",
    "max_positions",
    "max_contracts",
    "max_bp_pct",
    "avoid_earnings",
    "avoid_fomc",
)

STRATEGY_KEYS: list[str] = [s["key"] for s in CATALOG]
STRATEGY_SLUGS: list[str] = [s["slug"] for s in CATALOG]
VALID_TYPES: set[str] = set(CANONICAL_NAMES_BY_TYPE.keys())


# ── Helper functions ─────────────────────────────────────────────────────────

def get_by_key(key: str) -> dict | None:
    """Return the catalog entry for a primary key, or None if unknown."""
    return CATALOG_BY_KEY.get(key)


def get_by_slug(slug: str) -> dict | None:
    """Return the catalog entry for a slug, or None if unknown."""
    return CATALOG_BY_SLUG.get(slug)


def get_canonical_names(type_: str) -> set[str]:
    """Set of names that legitimately refer to the same engine as `type_`.
    Returns an empty set if the type isn't in the catalog."""
    return CANONICAL_NAMES_BY_TYPE.get(type_, set())


def is_known_type(type_: str) -> bool:
    """True iff `type_` matches a catalog key OR any catalog alias."""
    return type_ in VALID_TYPES


__all__ = [
    "__version__",
    "CATALOG",
    "CATALOG_BY_KEY",
    "CATALOG_BY_SLUG",
    "CANONICAL_NAMES_BY_KEY",
    "CANONICAL_NAMES_BY_TYPE",
    "ALL_CANONICAL_NAMES",
    "STRATEGY_OVERLAY_FIELDS",
    "STRATEGY_KEYS",
    "STRATEGY_SLUGS",
    "VALID_TYPES",
    "get_by_key",
    "get_by_slug",
    "get_canonical_names",
    "is_known_type",
]
