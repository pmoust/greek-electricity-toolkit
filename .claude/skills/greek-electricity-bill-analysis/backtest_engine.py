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
"""

VAT = 0.06  # reduced electricity VAT in Greece (verify current value)


def _econ(bill):
    """Return (A, vat, total, vat_base_excluding_A) using gross if it's an enanti bill."""
    if bill.get("is_enanti"):
        A = bill["gross_A_supply"]
        return A, bill["gross_vat"], bill["gross_total"], bill["gross_vat_base"] - A
    A = bill["A_supply"]
    return A, bill["vat"], bill["current_total"], bill["vat_base"] - A


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
