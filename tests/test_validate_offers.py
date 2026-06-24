"""Layer B — the offers gate works: the seed validates, and bad data is rejected."""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import validate_offers as vo  # noqa: E402


def test_seed_offers_pass_the_gate():
    r = subprocess.run([sys.executable, "scripts/validate_offers.py",
                        "data/offers_current.json"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_validator_rejects_bad_offer(tmp_path):
    bad = {"meta": {"last_verified": "2026-06-24"},
           "offers": [{"id": "X", "provider": "P", "product": "p",
                       "segment": "household",  # invalid
                       "energy_rate": -1, "paygio": 1, "color": "Pink",  # invalid
                       "source": "", "date": ""}]}
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    errors, _ = vo.validate(str(p))
    assert any("segment" in e for e in errors)
    assert any("color" in e for e in errors)
    assert any("energy_rate" in e for e in errors)
    assert any("source" in e for e in errors)


def test_staleness_detection():
    assert vo.days_old({"last_verified": "2026-06-24"},
                       today=__import__("datetime").date(2026, 8, 1)) == 38
