"""Layer A — deterministic unit tests for the backtest engine.

These lock the math and the classifications that matter most. The headline one
is test_the_trap: the #1 lesson of the whole project (a ΗΡΩΝ headline rate hides
the ρήτρα, so switching looks like a loss but is a win). If that ever flips, fail.
"""
import math

import backtest_engine as be


# ---- commitment_tier (regression guards) ----

def test_clause_free_floating_is_floating():
    # The bug we fixed: a floating product with no adjustment clause is STILL floating.
    o = {"color": "Yellow", "type": "floating", "adj_clause": False, "contract": "none"}
    assert be.commitment_tier(o) == "floating"


def test_green_is_floating():
    assert be.commitment_tier({"color": "Green", "type": "floating", "adj_clause": True}) == "floating"


def test_fixed_terms_bucket_by_length():
    assert be.commitment_tier({"color": "Blue", "type": "fixed", "contract": "12 months fixed"}) == "fixed-<=12m"
    assert be.commitment_tier({"color": "Blue", "type": "fixed-night", "contract": "24 months fixed"}) == "fixed-13-24m"
    assert be.commitment_tier({"color": "Blue", "type": "fixed", "contract": "36 months"}) == "fixed->24m"
    assert be.commitment_tier({"color": "Blue", "type": "fixed", "contract": "none"}) == "fixed-term?"


def test_tier_labels_cover_all_keys():
    for key in be.TIER_ORDER:
        assert key in be.TIER_LABELS


# ---- enanti detection / _econ ----

def test_is_enanti_by_gross_fields_and_flag():
    assert be._is_enanti({"enanti_credit": -224.95, "gross_total": 518.64})
    assert be._is_enanti({"is_enanti": True, "gross_total": 1.0})
    assert not be._is_enanti({"enanti_credit": 0.0})
    assert not be._is_enanti({})


def test_econ_uses_gross_for_enanti():
    bill = {"A_supply": 1, "vat": 1, "current_total": 1, "vat_base": 1,
            "enanti_credit": -224.95, "gross_A_supply": 336.93, "gross_vat": 29.18,
            "gross_total": 518.64, "gross_vat_base": 486.30}
    A, vat, total, xb = be._econ(bill)
    assert (A, vat, total) == (336.93, 29.18, 518.64)
    assert math.isclose(xb, 486.30 - 336.93)


# ---- new_supply_charge ----

def test_supply_charge_single_rate_and_paygio_proration():
    bill = {"kwh_total": 300, "kwh_day": 300, "kwh_night": 0, "days": 30}
    o = {"paygio": 6.0, "energy_rate": 0.10, "night_rate": None}
    # 6*30/30 + 300*0.10
    assert math.isclose(be.new_supply_charge(bill, o), 6.0 + 30.0)


def test_supply_charge_day_night_split():
    bill = {"kwh_total": 1000, "kwh_day": 700, "kwh_night": 300, "days": 30}
    o = {"paygio": 0.0, "energy_rate": 0.145, "night_rate": 0.105}
    assert math.isclose(be.new_supply_charge(bill, o), 700 * 0.145 + 300 * 0.105)


# ---- the trap (headline rate is misleading) ----

def test_the_trap_switching_saves_despite_higher_headline():
    # Actual ΗΡΩΝ bill: A=59.23 already embeds the ρήτρα (effective ~0.16/kWh).
    bill = {"A_supply": 59.23, "vat": 4.66, "current_total": 92.53, "vat_base": 77.68,
            "kwh_total": 337, "kwh_day": 337, "kwh_night": 0, "days": 34}
    competitor = {"paygio": 5.00, "energy_rate": 0.1133, "night_rate": None}
    new_total, saving, pct = be.backtest_bill(bill, competitor)
    assert saving > 0, "Comparing on the 0.0825 headline would wrongly say 'don't switch'"
    assert math.isclose(new_total, 76.23, abs_tol=0.01)


# ---- VAT invariant ----

def test_vat_recomputed_on_new_A_plus_B_plus_efk_only():
    bill = {"A_supply": 50.0, "vat": 4.0, "current_total": 90.0, "vat_base": 66.67,
            "kwh_total": 300, "kwh_day": 300, "kwh_night": 0, "days": 30}
    o = {"paygio": 5.0, "energy_rate": 0.10, "night_rate": None}
    new_total, _, _ = be.backtest_bill(bill, o)
    A_act, vat_act, total_act, xb = be._econ(bill)
    fixed_part = round(total_act - A_act - vat_act, 2)
    new_A = be.new_supply_charge(bill, o)
    assert math.isclose(new_total, fixed_part + new_A + be.VAT * (new_A + xb), abs_tol=0.01)


def test_same_rate_roundtrips_to_actual():
    # An offer that reproduces the current A should reproduce the current total.
    bill = {"A_supply": 0 + 5.0 + 300 * 0.12, "vat": 0, "current_total": 0,
            "kwh_total": 300, "kwh_day": 300, "kwh_night": 0, "days": 30, "vat_base": 0}
    bill["vat_base"] = bill["A_supply"]  # B=EFK=0 for this synthetic check
    bill["vat"] = round(be.VAT * bill["vat_base"], 2)
    bill["current_total"] = round(bill["A_supply"] + bill["vat"], 2)
    o = {"paygio": 5.0, "energy_rate": 0.12, "night_rate": None}
    new_total, saving, _ = be.backtest_bill(bill, o)
    assert abs(saving) < 0.02


# ---- offer_applies ----

def test_offer_applies_by_segment_and_meter():
    biz = {"customer_type": "Business/commercial LV", "register": "single", "efk_per_kwh": 0.005}
    res_dual = {"customer_type": "residential", "register": "dual (day/night)"}
    res_single = {"customer_type": "residential", "register": "single"}
    assert be.offer_applies({"segment": "business"}, biz)
    assert not be.offer_applies({"segment": "resi"}, biz)
    assert be.offer_applies({"segment": "resi"}, res_dual)
    assert be.offer_applies({"segment": "resi-night"}, res_dual)
    assert be.offer_applies({"segment": "resi"}, res_single)
    assert not be.offer_applies({"segment": "resi-night"}, res_single)
    assert not be.offer_applies({"segment": "business"}, res_single)


# ---- tiered_effective_rate ----

def test_tiered_rate_boundaries():
    tiers = [(700, 0.149), (None, 0.189)]
    assert math.isclose(be.tiered_effective_rate(500, tiers), 0.149)            # all in tier 1
    assert math.isclose(be.tiered_effective_rate(700, tiers), 0.149)            # exactly the boundary
    blended = (700 * 0.149 + 400 * 0.189) / 1100
    assert math.isclose(be.tiered_effective_rate(1100, tiers), blended)         # straddles
    assert be.tiered_effective_rate(0, tiers) == 0.0                            # guard


# ---- rank_within_tiers ----

def test_rank_within_tiers_orders_cheapest_first():
    bills = [{"A_supply": 100, "vat": 6, "current_total": 130, "vat_base": 110,
              "kwh_total": 500, "kwh_day": 500, "kwh_night": 0, "days": 30}]
    offers = {
        "cheap_float": {"paygio": 0, "energy_rate": 0.10, "color": "Yellow", "type": "floating", "adj_clause": True, "contract": "none"},
        "dear_float": {"paygio": 5, "energy_rate": 0.18, "color": "Yellow", "type": "floating", "adj_clause": True, "contract": "none"},
        "fixed12": {"paygio": 5, "energy_rate": 0.14, "color": "Blue", "type": "fixed", "contract": "12 months fixed"},
    }
    tiers = be.rank_within_tiers(bills, offers)
    assert "floating" in tiers and "fixed-<=12m" in tiers
    floating = [row[0] for row in tiers["floating"]]
    assert floating == ["cheap_float", "dear_float"]  # ascending by new_total


def test_zero_total_does_not_divide_by_zero():
    bill = {"A_supply": 0, "vat": 0, "current_total": 0, "vat_base": 0,
            "kwh_total": 0, "kwh_day": 0, "kwh_night": 0, "days": 0}
    o = {"paygio": 0, "energy_rate": 0.1, "night_rate": None}
    new_total, saving, pct = be.backtest_bill(bill, o)
    assert pct == 0.0
