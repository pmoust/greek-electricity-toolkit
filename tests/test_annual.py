"""Layer A — the seasonal annual comparator (annual_cost) and its building blocks.
A reference-consumption all-in figure, so we never extrapolate a short sample."""
import math

import backtest_engine as be


def test_yko_is_tiered_per_4month_band():
    assert math.isclose(be.yko_4mo(1600), 1600 * 0.00699)
    assert math.isclose(be.yko_4mo(1800), 1600 * 0.00699 + 200 * 0.05)
    assert math.isclose(be.yko_4mo(2100), 1600 * 0.00699 + 400 * 0.05 + 100 * 0.085)
    assert be.yko_4mo(0) == 0.0


def test_regulated_charge_has_capacity_and_energy_parts():
    b = be.regulated_charge(500, 0, kva=8, days=120, business=False)
    expect = (500 * 0.01151) + (8 * 6.21 * 120 / 365 + 500 * 0.00339) + (500 * 0.017) + be.yko_4mo(500)
    assert math.isclose(b, expect)
    # business uses the higher kVA capacity rate
    assert be.regulated_charge(500, 0, 25, 120, True) > be.regulated_charge(500, 0, 25, 120, False)


PROFILE = {
    "periods": [{"day": 1000, "night": 250, "days": 122},
                {"day": 900, "night": 250, "days": 121},
                {"day": 1100, "night": 250, "days": 122}],
    "kva": 25, "business": False, "municipal_eur_year": 60.0, "ert": True,
}


def test_annual_cost_is_all_in_and_monotonic():
    cheap = {"paygio": 5.0, "energy_rate": 0.12, "night_rate": None}
    dear = {"paygio": 5.0, "energy_rate": 0.18, "night_rate": None}
    a_cheap = be.annual_cost(cheap, PROFILE)
    a_dear = be.annual_cost(dear, PROFILE)
    # all-in figure is well above the bare energy cost
    total_kwh = sum(p["day"] + p["night"] for p in PROFILE["periods"])
    assert a_cheap > total_kwh * 0.12
    # higher energy rate => higher annual cost
    assert a_dear > a_cheap
    # municipal + ERT (VAT-exempt) are included
    assert a_cheap > 60.0 + be.REGULATED["ert_year"]


def test_dual_zone_offer_cheaper_than_flat_when_night_used():
    flat = {"paygio": 9.0, "energy_rate": 0.145, "night_rate": None}
    dual = {"paygio": 9.0, "energy_rate": 0.145, "night_rate": 0.105}
    assert be.annual_cost(dual, PROFILE) < be.annual_cost(flat, PROFILE)


def test_night_shift_saving_positive_for_dual_zero_for_flat():
    dual = {"paygio": 9.0, "energy_rate": 0.145, "night_rate": 0.105}
    flat = {"paygio": 9.0, "energy_rate": 0.145, "night_rate": None}
    assert be.night_shift_saving(dual, PROFILE, 0.20) > 0
    assert be.night_shift_saving(flat, PROFILE, 0.20) == 0.0
