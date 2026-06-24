"""Layer C — the example workbook builds, has the expected sheets, and the
backtest numbers don't silently drift (golden values)."""
import os
import subprocess
import sys

import backtest_engine as be
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES = os.path.join(ROOT, "examples")
XLSX = os.path.join(EXAMPLES, "example_model.xlsx")
EXPECTED_SHEETS = ["Bills_Raw", "Supplies", "Bill_Line_Items", "Fee_Model",
                   "Market_Offers", "Scenario_Model", "Backtest", "Tier_Ranking", "Recommendation"]

openpyxl = pytest.importorskip("openpyxl")


def test_committed_workbook_has_expected_sheets():
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    assert wb.sheetnames == EXPECTED_SHEETS


def test_builder_runs_clean_and_keeps_tree_unchanged():
    original = open(XLSX, "rb").read()
    try:
        r = subprocess.run([sys.executable, "build_example.py"], cwd=EXAMPLES,
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        wb = openpyxl.load_workbook(XLSX, read_only=True)
        assert wb.sheetnames == EXPECTED_SHEETS
    finally:
        open(XLSX, "wb").write(original)  # don't dirty the tracked artifact


def test_golden_backtest_totals(example_bills, example_offers):
    bills_by_supply = {}
    for b in example_bills["bills"]:
        bills_by_supply.setdefault(b["supply_id"], []).append(b)
    offers = {o["id"]: o for o in example_offers["offers"]}
    rec = example_offers["recommendations"]

    total_actual = total_new = 0.0
    for sid, sb in bills_by_supply.items():
        actual, new, _, _ = be.backtest_supply(sb, offers[rec[sid]])
        total_actual += actual
        total_new += new

    assert round(total_actual, 2) == 1079.65, "example actual total drifted"
    assert abs(total_new - 985.79) < 0.05, "example recommended total drifted"
    assert abs((total_actual - total_new) - 93.86) < 0.05, "example saving drifted"
