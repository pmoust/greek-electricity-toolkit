#!/usr/bin/env python3
"""Backtest a Greek electricity offer against an actual bill.

Core principle: only the competitive-supply block (A) changes when you switch
supplier. Regulated charges (B), taxes (EFK, 5-permille), municipal fees, ERT
and carried debt stay exactly as billed. VAT (6%) is recomputed on (A + B + EFK).

A "bill" dict needs these fields (all from the PDF, reconciled to the cent):
    A_supply      competitive supply charge actually billed (paygio+energy+ritra-disc)
    vat           VAT actually billed
    current_total this period's own charge (NOT final payable with arrears)
    vat_base      the 6% VAT base actually billed  (= A_supply + B + EFK)
    kwh_total, kwh_day, kwh_night, days
For an "enanti" clearing bill, pass the reconstructed gross instead:
    gross_A_supply, gross_vat, gross_total, gross_vat_base
and set is_enanti=True.

An "offer" dict:
    paygio        monthly standing charge (EUR)
    energy_rate   EFFECTIVE day/flat rate EUR/kWh (base + ritra - discounts, NOT headline)
    night_rate    EFFECTIVE night rate EUR/kWh, or None for single-register offers

LIMITATION: this models a flat or day/night rate. Tiered products (e.g. 0-700 /
>700 kWh, or day >200 kWh) and formula-indexed products (a*DAM+b, hourly MCP) are
NOT a single rate. Reduce them to an effective EUR/kWh FIRST -- with
tiered_effective_rate() for tiers, or by evaluating the formula at the current
wholesale index -- then pass the result as energy_rate.

Usage:
    from backtest_engine import backtest_bill, VAT
    new_total, saving, pct = backtest_bill(bill, offer)

Single source of truth for the workbook builder too. Public helpers:
    backtest_bill / backtest_supply / supply_actual  -- the core backtest
    commitment_tier + TIER_ORDER/TIER_LABELS          -- floating vs fixed-by-term
    rank_within_tiers                                  -- strategy-before-price ranking
    offer_applies(offer, supply)                       -- segment + meter eligibility
    tiered_effective_rate                              -- blend a tiered product
    annual_cost(offer, profile) / regulated_charge     -- seasonal all-in annual comparator
    night_shift_saving                                 -- value of moving load to the night register
"""

VAT = 0.06  # reduced electricity VAT in Greece (verify current value)


def _is_enanti(bill):
    """An enanti clearing bill whose printed payable nets out a prior on-account
    charge: use its reconstructed gross. Detected by an explicit flag OR by the
    presence of gross_* fields alongside a non-zero enanti_credit."""
    return bool(bill.get("is_enanti")) or (
        bill.get("enanti_credit") and bill.get("gross_total") is not None)


def _econ(bill):
    """Return (A, vat, total, vat_base_excluding_A) using gross if it's an enanti bill."""
    if _is_enanti(bill):
        A = bill["gross_A_supply"]
        return A, bill["gross_vat"], bill["gross_total"], bill["gross_vat_base"] - A
    A = bill["A_supply"]
    return A, bill["vat"], bill["current_total"], bill["vat_base"] - A


def supply_actual(bills):
    """Sum of the economic current-period cost across a supply's bills."""
    return round(sum(_econ(b)[2] for b in bills), 2)


def offer_applies(offer, supply):
    """Is this offer a candidate for this supply? Matches segment + meter type:
    business supplies need business offers; dual-register (Γ1Ν) supplies can take
    residential single OR dual-zone offers; single-register residential takes resi."""
    seg = offer.get("segment", "")
    is_business = "business" in str(supply.get("customer_type", "")).lower() \
        or supply.get("efk_per_kwh") == 0.005
    if is_business:
        return seg == "business"
    if "dual" in str(supply.get("register", "")):
        return seg in ("resi", "resi-night")
    return seg == "resi"


def new_supply_charge(bill, offer):
    """Block A under the offer. Day/night aware; prorates paygio by days/30."""
    rd = offer["energy_rate"]
    rn = offer.get("night_rate")
    if rn is not None and bill.get("kwh_night", 0) > 0:
        energy = bill["kwh_day"] * rd + bill["kwh_night"] * rn
    else:
        energy = bill["kwh_total"] * rd
    return offer["paygio"] * bill["days"] / 30.0 + energy


def backtest_bill(bill, offer):
    """Return (new_total, saving_eur, saving_pct) for one bill under one offer."""
    A_act, vat_act, total_act, vat_base_exclA = _econ(bill)
    fixed_part = round(total_act - A_act - vat_act, 2)   # B + taxes + municipal + ERT
    new_A = new_supply_charge(bill, offer)
    new_vat = VAT * (new_A + vat_base_exclA)             # B and EFK stay in the base
    new_total = fixed_part + new_A + new_vat
    saving = total_act - new_total
    pct = saving / total_act * 100 if total_act else 0.0
    return round(new_total, 2), round(saving, 2), round(pct, 1)


def backtest_supply(bills, offer):
    """Aggregate across all bills of one supply. Returns (actual, new, saving, pct)."""
    actual = sum(_econ(b)[2] for b in bills)
    new = sum(backtest_bill(b, offer)[0] for b in bills)
    saving = round(actual - new, 2)
    pct = round(saving / actual * 100, 1) if actual else 0.0
    return round(actual, 2), round(new, 2), saving, pct


def tiered_effective_rate(kwh_month, tiers):
    """Blended EUR/kWh for a tiered product at a given monthly consumption.
    tiers = [(upto_kwh_or_None, rate), ...] in ascending order; None = open top tier.
    Example: 0-700 @0.149, >700 @0.189  ->  tiers=[(700,0.149),(None,0.189)]
    """
    remaining, cost, lo = kwh_month, 0.0, 0
    for upto, rate in tiers:
        band = (upto - lo) if upto is not None else remaining
        take = max(0.0, min(remaining, band))
        cost += take * rate
        remaining -= take
        lo = upto if upto is not None else lo
        if remaining <= 0:
            break
    return cost / kwh_month if kwh_month else 0.0


def rank_offers(bills, offers):
    """Rank offers (dict name->offer) for a supply, cheapest first.
    Returns list of (name, new_total, saving, pct).
    NOTE: a flat ranking mixes risk tiers. For a real recommendation rank WITHIN
    a commitment tier (floating vs fixed-1y vs fixed-2y+) -- see rank_within_tiers."""
    rows = []
    for name, offer in offers.items():
        _, new, saving, pct = backtest_supply(bills, offer)
        rows.append((name, new, saving, pct))
    rows.sort(key=lambda r: r[1])
    return rows


def commitment_tier(offer):
    """Classify an offer on the risk/commitment axis.
    Floating and fixed-of-different-terms are NOT interchangeable -- decide the
    tier first, then compare price within it. Returns one of:
    'floating', 'fixed-<=12m', 'fixed-13-24m', 'fixed->24m'."""
    # Fixed = locked for a term (Blue, or an explicitly fixed type). A floating
    # product without a separate adjustment clause is STILL floating (it resets
    # monthly) -- do not infer "fixed" from the absence of a clause.
    is_fixed = offer.get("color") == "Blue" or "fixed" in str(offer.get("type", ""))
    if not is_fixed:
        return "floating"
    months = 0
    for tok in str(offer.get("contract", "")).replace("-", " ").split():
        if tok.isdigit():
            months = int(tok); break
    if months == 0:
        return "fixed-term?"
    if months <= 12:
        return "fixed-<=12m"
    if months <= 24:
        return "fixed-13-24m"
    return "fixed->24m"


# Display order + human labels for the commitment tiers (shared by report/workbook).
TIER_ORDER = ["floating", "fixed-<=12m", "fixed-13-24m", "fixed->24m", "fixed-term?"]
TIER_LABELS = {
    "floating": "Floating — follow the market",
    "fixed-<=12m": "Fixed ≤ 12 months",
    "fixed-13-24m": "Fixed 13–24 months",
    "fixed->24m": "Fixed > 24 months",
    "fixed-term?": "Fixed — term unspecified",
}


def rank_within_tiers(bills, offers):
    """Group offers by commitment tier and rank cheapest-first WITHIN each tier.
    Returns {tier: [(name, new_total, saving, pct, term), ...]}. Pick your tier
    (commit-to-a-price vs follow-the-market) first, then the cheapest in it."""
    tiers = {}
    for name, offer in offers.items():
        _, new, saving, pct = backtest_supply(bills, offer)
        tier = commitment_tier(offer)
        tiers.setdefault(tier, []).append((name, new, saving, pct, offer.get("contract", "")))
    for rows in tiers.values():
        rows.sort(key=lambda r: r[1])
    return tiers


# Regulated reference rates (mid-2026; same as greek-tariff-reference.md). These are
# provider-INDEPENDENT — single source of truth, shared with the example generator.
REGULATED = {
    "transmission_per_kwh": 0.01151,        # ADMIE
    "distribution_per_kwh": 0.00339,        # DEDDIE energy part
    "distribution_kva_year_resi": 6.21,     # DEDDIE capacity (residential)
    "distribution_kva_year_business": 11.339,
    "etmear_per_kwh": 0.017,
    "yko_tiers_4mo": [(1600, 0.00699), (2000, 0.05), (None, 0.085)],  # per 4-month band
    "efk_resi": 0.0022,
    "efk_business": 0.005,
    "ert_year": 36.0,
}


def yko_4mo(kwh_4mo):
    """ΥΚΩ (public-service levy) cost for a 4-month period's kWh — tiered."""
    return tiered_effective_rate(kwh_4mo, REGULATED["yko_tiers_4mo"]) * kwh_4mo if kwh_4mo else 0.0


def regulated_charge(day_kwh, night_kwh, kva, days, business=False):
    """Block B (ADMIE + DEDDIE + ETMEAR + YKO) for one period. Provider-independent."""
    kwh = day_kwh + night_kwh
    kva_rate = REGULATED["distribution_kva_year_business"] if business else REGULATED["distribution_kva_year_resi"]
    transmission = kwh * REGULATED["transmission_per_kwh"]
    distribution = kva * kva_rate * days / 365 + kwh * REGULATED["distribution_per_kwh"]
    etmear = kwh * REGULATED["etmear_per_kwh"]
    return transmission + distribution + etmear + yko_4mo(kwh)


def annual_cost(offer, profile):
    """All-in annual cost (€, incl. regulated + 6% VAT + municipal + ΕΡΤ) of an offer
    at a REFERENCE consumption profile — a seasonally-weighted comparator that does not
    rely on a short, unrepresentative bill sample.

    profile = {
      "periods": [{"day": kWh, "night": kWh, "days": N}, ...]  # e.g. three 4-month bands
      "kva": 25, "business": False,
      "municipal_eur_year": 60.0, "ert": True,
    }
    Night kWh is priced at the offer's night_rate when it has one, else the day rate
    (so a dual-zone offer's value — and the gain from shifting load to night — shows up).
    """
    business = profile.get("business", False)
    efk_rate = REGULATED["efk_business"] if business else REGULATED["efk_resi"]
    rate_day = offer["energy_rate"]
    rate_night = offer.get("night_rate") or offer["energy_rate"]
    total = 0.0
    for p in profile["periods"]:
        day, night, days = p["day"], p.get("night", 0), p["days"]
        A = offer["paygio"] * days / 30.0 + day * rate_day + night * rate_night
        B = regulated_charge(day, night, profile["kva"], days, business)
        efk = (day + night) * efk_rate
        total += A + B + efk + VAT * (A + B + efk)
    total += profile.get("municipal_eur_year", 0.0)
    if profile.get("ert", True):
        total += REGULATED["ert_year"]
    return round(total, 2)


def night_shift_saving(offer, profile, fraction):
    """€/year saved by shifting `fraction` of day kWh to the night register (dual-zone
    offers only). Returns 0 for single-register offers."""
    if not offer.get("night_rate"):
        return 0.0
    shifted = {**profile, "periods": [
        {"day": p["day"] * (1 - fraction), "night": p.get("night", 0) + p["day"] * fraction, "days": p["days"]}
        for p in profile["periods"]]}
    return round(annual_cost(offer, profile) - annual_cost(offer, shifted), 2)


if __name__ == "__main__":
    # Worked example: the baseline trap. A ΗΡΩΝ PROTECT bill whose HEADLINE looks
    # like 0,0825 but whose EFFECTIVE rate (base+ritra-disc) is ~0,157.
    bill = dict(A_supply=59.23, vat=4.66, current_total=92.53, vat_base=77.68,
                kwh_total=337, kwh_day=337, kwh_night=0, days=34)
    zenith = dict(paygio=5.00, energy_rate=0.1133, night_rate=None)
    nt, sav, pct = backtest_bill(bill, zenith)
    print(f"Under Zenith @0.1133: new={nt}  saving={sav} ({pct}%)")
    # -> saving is POSITIVE: switching is cheaper, because the actual ΗΡΩΝ A (59.23)
    #    embeds the ~0,0789 ritra. Comparing 0,1133 to the headline 0,0825 gives the
    #    opposite (wrong) answer.
