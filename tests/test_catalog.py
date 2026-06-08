"""Pin the catalog shape so bot + platform stay in sync.

These tests are the contract between the package and its consumers:
adding a new strategy or changing the catalog shape requires updating
both sides of the contract.
"""
from __future__ import annotations

import pytest

from strategy_catalog import (
    CATALOG,
    CATALOG_BY_KEY,
    CATALOG_BY_SLUG,
    CANONICAL_NAMES_BY_KEY,
    CANONICAL_NAMES_BY_TYPE,
    ALL_CANONICAL_NAMES,
    STRATEGY_KEYS,
    STRATEGY_SLUGS,
    STRATEGY_OVERLAY_FIELDS,
    VALID_TYPES,
    get_by_key,
    get_by_slug,
    get_canonical_names,
    is_known_type,
    __version__,
)


def test_version_is_semver():
    parts = __version__.split(".")
    assert len(parts) == 3
    for p in parts:
        int(p)  # raises if not numeric


def test_catalog_entries_have_required_keys():
    required = {"key", "name", "slug", "aliases", "description", "risk", "defaults"}
    for entry in CATALOG:
        missing = required - set(entry.keys())
        assert not missing, f"entry {entry.get('key', '?')!r} missing keys: {missing}"


def test_catalog_keys_are_unique():
    keys = [s["key"] for s in CATALOG]
    assert len(keys) == len(set(keys)), "duplicate key in CATALOG"


def test_catalog_slugs_are_unique():
    slugs = [s["slug"] for s in CATALOG]
    assert len(slugs) == len(set(slugs)), "duplicate slug in CATALOG"


def test_slugs_are_snake_case():
    import re
    pat = re.compile(r"^[a-z][a-z0-9_]*$")
    for s in CATALOG:
        assert pat.match(s["slug"]), f"slug {s['slug']!r} is not snake_case"


def test_defaults_have_overlay_field_subset():
    """Every entry's defaults dict can ONLY contain keys from the overlay
    set. Strategy-specific knobs (drop_pct_threshold, l1_trigger_drop,
    etc.) belong in the bot's engine dataclass, NOT here."""
    allowed = set(STRATEGY_OVERLAY_FIELDS)
    for s in CATALOG:
        extra = set(s["defaults"].keys()) - allowed
        assert not extra, f"entry {s['key']!r} has non-overlay keys in defaults: {extra}"


def test_canonical_names_include_primary_and_aliases():
    for entry in CATALOG:
        names = CANONICAL_NAMES_BY_KEY[entry["key"]]
        assert entry["key"] in names
        for alias in entry["aliases"]:
            assert alias in names


def test_aliases_reverse_lookup():
    """Any alias resolves to the SAME canonical set as its primary key."""
    for entry in CATALOG:
        for alias in entry["aliases"]:
            assert CANONICAL_NAMES_BY_TYPE[alias] == CANONICAL_NAMES_BY_KEY[entry["key"]]


def test_known_strategies_present():
    """Pin the known strategies. Adding one requires updating this list
    so downstream consumers see the addition deliberately."""
    expected = {
        "Iron Condor",
        "Vertical Spread",
        "Covered Call Wheel",
        "Zero DTE",
        "Liquidity Raid",
        "Momentum Breakout",
        "Supply Demand",
        "Futures Scalp",
        "Nasdaq Short Put",
    }
    assert set(STRATEGY_KEYS) == expected


def test_futures_scalp_aliases_cover_paper_variants():
    """The two FSCALP paper-bot variants share the same engine — both
    must resolve to Futures Scalp's canonical set."""
    expected_aliases = {"Nasdaq Day Trade", "S&P Day Trade"}
    assert expected_aliases <= set(CATALOG_BY_KEY["Futures Scalp"]["aliases"])
    for alias in expected_aliases:
        assert CANONICAL_NAMES_BY_TYPE[alias] == CANONICAL_NAMES_BY_KEY["Futures Scalp"]


def test_get_by_key_returns_entry():
    e = get_by_key("Iron Condor")
    assert e is not None
    assert e["slug"] == "iron_condor"


def test_get_by_key_returns_none_for_unknown():
    assert get_by_key("Bogus") is None


def test_get_by_slug_returns_entry():
    e = get_by_slug("vps")
    assert e is not None
    assert e["key"] == "Vertical Spread"


def test_is_known_type_accepts_primary_and_aliases():
    assert is_known_type("Iron Condor")
    assert is_known_type("Strangle")         # alias
    assert is_known_type("Nasdaq Day Trade") # alias
    assert not is_known_type("Bogus")


def test_get_canonical_names_returns_set():
    names = get_canonical_names("Iron Condor")
    assert isinstance(names, set)
    assert "Iron Condor" in names
    assert "Strangle" in names


def test_valid_types_covers_keys_and_aliases():
    for entry in CATALOG:
        assert entry["key"] in VALID_TYPES
        for alias in entry["aliases"]:
            assert alias in VALID_TYPES


def test_grantable_expands_variants():
    """GRANTABLE is the per-VARIANT view: split strategies (VPS, 0DTE) emit one
    entry per variant; everything else passes through 1:1. 7 non-variant + 4
    variant = 11."""
    from strategy_catalog import GRANTABLE, GRANTABLE_KEYS
    assert len(GRANTABLE) == 11
    keys = set(GRANTABLE_KEYS)
    # variant keys == the bot config strategy NAMES (the grant↔bot contract)
    assert {"Vertical Put Spread - Day", "Vertical Put Spread - Swing"} <= keys
    assert {"0 DTE SPX", "0 DTE - End of Day"} <= keys
    # the combined engine keys are NOT grantable units (replaced by variants)
    assert "Vertical Spread" not in keys
    assert "Zero DTE" not in keys
    # non-variant strategies pass through unchanged
    assert "Iron Condor" in keys and "Futures Scalp" in keys


def test_grantable_keys_and_slugs_unique():
    from strategy_catalog import GRANTABLE
    keys = [g["key"] for g in GRANTABLE]
    slugs = [g["slug"] for g in GRANTABLE]
    assert len(keys) == len(set(keys))
    assert len(slugs) == len(set(slugs))


def test_engine_type_for_maps_variant_to_engine():
    from strategy_catalog import engine_type_for
    assert engine_type_for("Vertical Put Spread - Day") == "Vertical Spread"
    assert engine_type_for("Vertical Put Spread - Swing") == "Vertical Spread"
    assert engine_type_for("0 DTE SPX") == "Zero DTE"
    assert engine_type_for("0 DTE - End of Day") == "Zero DTE"
    # non-variant: engine_type == key
    assert engine_type_for("Iron Condor") == "Iron Condor"
    assert engine_type_for("Bogus") is None


def test_engine_types_are_all_valid_bot_types():
    """Every grantable's engine_type must remain a valid bot config type — this
    is what keeps the bot's config validation green after the split."""
    from strategy_catalog import GRANTABLE, VALID_TYPES
    for g in GRANTABLE:
        assert g["engine_type"] in VALID_TYPES, g["key"]


def test_grantable_keys_for_product():
    from strategy_catalog import grantable_keys_for_product
    assert grantable_keys_for_product("Vertical Spread") == [
        "Vertical Put Spread - Day", "Vertical Put Spread - Swing"]
    assert grantable_keys_for_product("Zero DTE") == [
        "0 DTE SPX", "0 DTE - End of Day"]
    assert grantable_keys_for_product("Iron Condor") == ["Iron Condor"]


def test_variant_display_labels_and_product_grouping():
    from strategy_catalog import GRANTABLE_BY_KEY
    day = GRANTABLE_BY_KEY["Vertical Put Spread - Day"]
    assert day["name"] == "VPS — Day"
    assert day["product_name"] == "Vertical Put Spread"   # marketing groups here
    assert day["is_variant"] is True
    ic = GRANTABLE_BY_KEY["Iron Condor"]
    assert ic["is_variant"] is False and ic["product_name"] == "Iron Condor"


def test_catalog_engine_view_unchanged_by_split():
    """The split must NOT change the engine/product CATALOG keys — the bot's
    type-validation + the public marketing cards depend on them."""
    assert set(STRATEGY_KEYS) == {
        "Iron Condor", "Vertical Spread", "Covered Call Wheel", "Zero DTE",
        "Liquidity Raid", "Momentum Breakout", "Supply Demand", "Futures Scalp",
        "Nasdaq Short Put",
    }


def test_overlay_fields_are_stable():
    """Pin the overlay-field set — changing it requires coordinated
    schema migrations across bot + platform."""
    assert STRATEGY_OVERLAY_FIELDS == (
        "profit_target_pct",
        "stop_loss_mult",
        "max_positions",
        "max_contracts",
        "max_bp_pct",
        "avoid_earnings",
        "avoid_fomc",
    )
