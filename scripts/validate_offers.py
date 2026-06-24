#!/usr/bin/env python3
"""Validate data/offers_current.json — the gate the weekly refresh workflow must
pass before opening a PR (and a CI check on every push).

Schema errors -> exit 1. Optional freshness check (--check-stale) -> exit 3 if older
than --max-age-days. Usage: python scripts/validate_offers.py [path] [--check-stale]
"""
import argparse
import datetime
import json
import sys

SEGMENTS = {"resi", "resi-night", "business"}
COLORS = {"Blue", "Green", "Yellow", "Orange"}
REQUIRED = {"id", "provider", "product", "segment", "energy_rate", "paygio", "color", "source", "date"}
# How the price is set over time (finer than color; affects predictability).
PRICING_BASES = {"fixed", "green-monthly", "index-prev-month", "dynamic-hourly"}


def validate_offer_optionals(o):
    """Validate the optional incentive/term/behaviour fields when present."""
    errors = []
    oid = o.get("id", "<no id>")
    if "gift_eur" in o and (not isinstance(o["gift_eur"], (int, float)) or o["gift_eur"] < 0):
        errors.append(f"{oid}: gift_eur must be a number >= 0")
    if "exit_fee_per_month" in o and (not isinstance(o["exit_fee_per_month"], (int, float)) or o["exit_fee_per_month"] < 0):
        errors.append(f"{oid}: exit_fee_per_month must be a number >= 0")
    if "pricing_basis" in o and o["pricing_basis"] not in PRICING_BASES:
        errors.append(f"{oid}: pricing_basis must be one of {sorted(PRICING_BASES)}")
    for k in ("gift_conditions", "caveat"):
        if k in o and not isinstance(o[k], str):
            errors.append(f"{oid}: {k} must be a string")
    return errors


def validate(path):
    """Return (errors, data). errors is a list of human-readable strings."""
    errors = []
    data = json.load(open(path, encoding="utf-8"))
    if "last_verified" not in data.get("meta", {}):
        errors.append("meta.last_verified missing")
    offers = data.get("offers")
    if not isinstance(offers, list) or not offers:
        errors.append("offers must be a non-empty list")
        return errors, data
    seen = set()
    for o in offers:
        oid = o.get("id", "<no id>")
        miss = REQUIRED - o.keys()
        if miss:
            errors.append(f"{oid}: missing keys {sorted(miss)}")
        if o.get("segment") not in SEGMENTS:
            errors.append(f"{oid}: bad segment {o.get('segment')!r}")
        if o.get("color") not in COLORS:
            errors.append(f"{oid}: bad color {o.get('color')!r}")
        if not isinstance(o.get("energy_rate"), (int, float)) or o.get("energy_rate", 0) <= 0:
            errors.append(f"{oid}: energy_rate must be a positive number")
        if not isinstance(o.get("paygio"), (int, float)) or o.get("paygio", -1) < 0:
            errors.append(f"{oid}: paygio must be >= 0")
        if not o.get("source"):
            errors.append(f"{oid}: source URL required (provenance)")
        if not o.get("date"):
            errors.append(f"{oid}: access date required (provenance)")
        if oid in seen:
            errors.append(f"duplicate offer id {oid}")
        seen.add(oid)
        errors.extend(validate_offer_optionals(o))
    return errors, data


def days_old(meta, today=None):
    today = today or datetime.date.today()
    try:
        lv = datetime.date.fromisoformat(meta.get("last_verified", ""))
    except ValueError:
        return None
    return (today - lv).days


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default="data/offers_current.json")
    ap.add_argument("--check-stale", action="store_true", help="also fail if data is stale")
    ap.add_argument("--max-age-days", type=int, default=35, help="floating rates reset monthly")
    args = ap.parse_args(argv)

    errors, data = validate(args.path)
    for e in errors:
        print("ERROR:", e)
    if errors:
        print(f"FAIL: {len(errors)} schema error(s) in {args.path}")
        return 1
    print(f"OK: {len(data['offers'])} offers valid in {args.path}")

    if args.check_stale:
        d = days_old(data.get("meta", {}))
        if d is None:
            print("WARN: meta.last_verified unparseable")
        elif d > args.max_age_days:
            print(f"STALE: data is {d} days old (> {args.max_age_days}); refresh recommended")
            return 3
        else:
            print(f"Freshness OK: {d} days old")
    return 0


if __name__ == "__main__":
    sys.exit(main())
