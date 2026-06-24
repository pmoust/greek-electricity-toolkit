"""Layer B — data integrity, PII safety, and doc consistency.

These run on the synthetic example data and on the tracked files. They double as
the validation gate for the weekly offer-refresh workflow (see scripts/validate_offers.py).
"""
import json
import os
import re
import subprocess

import backtest_engine as be

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEGMENTS = {"resi", "resi-night", "business"}
COLORS = {"Blue", "Green", "Yellow", "Orange"}
REQUIRED_OFFER_KEYS = {"id", "provider", "product", "segment", "energy_rate", "paygio", "color", "source", "date"}


def _tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [f for f in out.stdout.splitlines() if f]


# ---- bill reconciliation (cent-accurate) ----

def test_example_bills_reconcile_to_the_cent(example_bills):
    for b in example_bills["bills"]:
        blocks = (b["A_supply"] + b["B_regulated"] + b["G_supplementary"]
                  + b["E_municipal"] + b["ST_ert"] + b["vat"])
        assert abs(blocks - b["current_total"]) < 0.005, b["file"]
        assert abs(b["vat"] - round(be.VAT * b["vat_base"], 2)) < 0.005, b["file"]


# ---- offer schema ----

def test_example_offers_schema(example_offers):
    seen = set()
    for o in example_offers["offers"]:
        missing = REQUIRED_OFFER_KEYS - o.keys()
        assert not missing, f"{o.get('id')}: missing {missing}"
        assert o["id"] not in seen, f"duplicate offer id {o['id']}"
        seen.add(o["id"])
        assert o["segment"] in SEGMENTS, f"{o['id']}: bad segment {o['segment']}"
        assert o["color"] in COLORS, f"{o['id']}: bad color {o['color']}"
        assert isinstance(o["energy_rate"], (int, float)) and o["energy_rate"] > 0
        assert isinstance(o["paygio"], (int, float)) and o["paygio"] >= 0


def test_recommendations_exist_and_fit_the_meter(example_bills, example_offers):
    supplies = {s["id"]: s for s in example_bills["supplies"]}
    offers = {o["id"]: o for o in example_offers["offers"]}
    for sid, oid in example_offers["recommendations"].items():
        assert sid in supplies, f"rec for unknown supply {sid}"
        assert oid in offers, f"rec points to unknown offer {oid}"
        # a recommendation must be eligible for that supply's segment + meter
        assert be.offer_applies(offers[oid], supplies[sid]), \
            f"recommended {oid} does not fit supply {sid}"


# ---- PII guard (pattern-based; never hardcodes real personal data) ----

def test_personal_deliverables_are_not_tracked():
    tracked = set(_tracked_files())
    for forbidden in ("greek_electricity_contract_analysis_report.md",
                      "greek_electricity_contract_analysis_model.xlsx"):
        assert forbidden not in tracked, f"{forbidden} must stay gitignored (contains real data)"


def test_no_pii_patterns_in_tracked_files():
    # High-confidence personal patterns that synthetic example data must never match.
    patterns = {
        "RF e-payment code": re.compile(r"RF\d{18,}"),
        "GR IBAN": re.compile(r"\bGR\d{20,}\b"),
        "real ΔΕΔΔΗΕ supply no.": re.compile(r"\b[1-9]-\d{8}-\d{2}\b"),  # 0-0000...-0 placeholder is allowed
        "long account/supply id": re.compile(r"\b\d{12,}\b"),
        "ΑΦΜ with 9 digits": re.compile(r"ΑΦΜ\D{0,4}\d{9}"),
    }
    # Optional local denylist of literal terms (gitignored; absent in CI).
    denylist = []
    dl = os.path.join(ROOT, ".pii-denylist")
    if os.path.exists(dl):
        denylist = [t.strip() for t in open(dl, encoding="utf-8") if t.strip()]
    text_ext = (".md", ".py", ".json", ".yml", ".yaml", ".txt", ".cfg", ".ini")
    offenders = []
    for f in _tracked_files():
        if not f.endswith(text_ext):
            continue
        content = open(os.path.join(ROOT, f), encoding="utf-8", errors="ignore").read()
        for label, rx in patterns.items():
            if rx.search(content):
                offenders.append(f"{f}: {label}")
        for term in denylist:
            if term in content:
                offenders.append(f"{f}: denylisted term")
    assert not offenders, "possible PII in tracked files: " + "; ".join(offenders)


# ---- doc consistency (drift guards) ----

def _read(rel):
    return open(os.path.join(ROOT, rel), encoding="utf-8").read()


def test_sheet_name_consistency():
    # The tier sheet must be referenced everywhere it's described, and no stale "8-sheet".
    skill = _read(".claude/skills/greek-electricity-bill-analysis/SKILL.md")
    readme = _read("README.md")
    report = _read("examples/example_report.md")
    for doc, name in ((skill, "SKILL.md"), (readme, "README.md"), (report, "example_report.md")):
        assert "Tier_Ranking" in doc, f"{name} should mention Tier_Ranking"
    assert "8-sheet" not in readme and "8 sheets" not in readme, "stale sheet count in README"


def test_supplier_list_consistency():
    # The supplier roster must not drift between the README appendix and the skill reference.
    readme = _read("README.md")
    reference = _read(".claude/skills/greek-electricity-bill-analysis/greek-tariff-reference.md")
    canonical = ["ΔΕΗ", "ΗΡΩΝ", "Protergia", "Enerwave", "NRG", "Volton", "Zenith",
                 "ELIN", "Eunice", "Volterra", "WATT+VOLT", "Octopus"]
    for name in canonical:
        assert name in readme, f"{name} missing from README appendix"
        assert name in reference, f"{name} missing from skill reference"
