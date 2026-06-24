---
name: greek-electricity-bill-analysis
description: Use when comparing Greek electricity providers/tariffs, parsing ΔΕΗ/ΗΡΩΝ/Protergia/Elpedison/etc bills (λογαριασμός ρεύματος), deciding whether to switch supplier, or backtesting what a bill would have cost on another offer. Covers προμήθεια vs ρυθμιζόμενες χρεώσεις, the Διακύμανση/ρήτρα adjustment clause, ΕΦΚ, ΦΠΑ 6%, ΥΚΩ/ΕΤΜΕΑΡ, Γ1Ν night tariff, έναντι/εκκαθαριστικός bills, and RAAEY Μπλε/Πράσινο/Κίτρινο colors.
license: MIT
---

# Greek Electricity Bill Analysis

## Overview

A Greek electricity bill splits into **one provider-controlled block and three pass-through blocks**. Comparing suppliers correctly means isolating the provider block, computing the *effective* energy rate (not the headline), and holding everything else fixed.

**The #1 mistake (verified): trusting the headline energy rate.** Floating products (ΗΡΩΝ PROTECT, most "Κίτρινο/Yellow" tariffs) print a low base rate like `0,0825 €/kWh` and add a separate **"Διακύμανση Κόστους Αγοράς" / ρήτρα αναπροσαρμογής** line that often *doubles* it. A bill that looks like 0,0825 is really ~0,157 effective. Ignore the clause and your switch recommendation flips to the wrong answer.

## The four blocks (only block A changes when you switch)

| Block | Lines | Provider-dependent? | In ΦΠΑ base? |
|---|---|---|---|
| **A. Προμήθεια (competitive supply)** | πάγιο + energy €/kWh + **Διακύμανση/ρήτρα** + discounts | **YES — the whole comparison** | yes |
| **B. Ρυθμιζόμενες (regulated)** | ΑΔΜΗΕ (Σύστημα Μεταφοράς/transmission), ΔΕΔΔΗΕ (Δίκτυο Διανομής/distribution €/kVA+€/kWh), ΕΤΜΕΑΡ, ΥΚΩ | NO — identical for all suppliers | yes |
| **C. Taxes** | ΕΦΚ (excise), Ειδικό Τέλος 5‰ | NO | ΕΦΚ yes; 5‰ **no** |
| **D. Pass-through** | Δημοτικά Τέλη/Φόρος (ΔΤ/ΔΦ), ΤΑΠ, ΕΡΤ, late interest, roundings | NO — property/municipality based | **no** |

See [greek-tariff-reference.md](greek-tariff-reference.md) for current unit rates, ΕΦΚ values, RAAEY colors, night-tariff hours, and provider consolidation (WATT+VOLT→Protergia, Elpedison→Enerwave).

## Procedure

1. **Extract** with `pdftotext -layout bill.pdf` — ΔΕΗ and ΗΡΩΝ bills are text PDFs, no OCR needed. Pull: provider, παροχή (supply no.), product, period+days, kWh (day/night split if dual), each block's lines, ΦΠΑ base, totals, and `Προηγούμενο Ανεξόφλητο` (carried debt).
2. **Reconcile to the cent:** `A + B + Γ(supplementary) + E(municipal) + ΣΤ(ERT) + ΦΠΑ = current-period total`. If it doesn't balance, you missed a line (often a discount like `Έκπτωση ΕΝ.Α` or a credit).
3. **Compute the EFFECTIVE energy rate** = `base €/kWh + Διακύμανση/ρήτρα €/kWh − discounts`. Never compare on the headline base alone.
4. **Verify ΦΠΑ:** it is **6%** (reduced) of `(A + B + ΕΦΚ)`. Municipal, ΕΡΤ, 5‰, and interest are OUTSIDE the base. ΕΦΚ ≈ 0,0022 €/kWh residential, 0,005 €/kWh business.
5. **Backtest an offer** — replace only block A, recompute ΦΠΑ, keep B/C/D as billed:
   ```
   fixed_part = actual_total − actual_A − actual_VAT          # B + C + D, unchanged
   new_A      = offer_paygio × days/30 + energy_at_offer_rate # day/night aware
   new_VAT    = 0.06 × (new_A + (actual_VAT_base − actual_A))  # B+ΕΦΚ stay
   new_total  = fixed_part + new_A + new_VAT
   ```
   The reusable engine is [backtest_engine.py](backtest_engine.py).
6. **Decide STRATEGY before price — then compare within the tier (not across it).** Floating, 1-year fixed and 2-year fixed are different products on a *risk axis*, not interchangeable price points; ranking them in one flat list is apples-to-oranges. **First** ask: do you want to *commit to a price* (fixed/Μπλε) or *follow the market* (floating/Κίτρινο-Πράσινο)? **Then** rank within each commitment tier and present the cheapest of each *with its term*, so the choice is risk-stance first, price second. Treat contract **duration/lock-in** as a first-class factor: a multi-year fixed rate is only "cheaper" if you'd actually hold it, and a long lock in a volatile market (fuel/geopolitical shocks) carries opportunity risk — not free certainty.
7. **Compare across the WHOLE market — don't name a winner from memory.** Pull the current active-supplier list from the official ΡΑΑΕΥ tool **energycost.gr** (the field consolidates — see reference); the cheapest option is frequently a **non-incumbent or a recent entrant**, not ΔΕΗ/ΗΡΩΝ. For each candidate: (a) filter by **segment** (residential vs business/κοινόχρηστα) and **meter type** (single vs dual-zone) — an offer your meter can't take is not a candidate; (b) compute its **effective** rate; (c) group by commitment tier and `rank_within_tiers(...)` (see engine) — *not* one flat `rank_offers` across tiers; (d) tag each with **term length**, an **eligibility** flag (accepts your κοινόχρηστα/kVA/dual meter?) and a **data-confidence** flag (live energycost.gr value vs aggregator/stale vs formula-indexed). Never present a rate you cannot source as if it were available.

## Gotchas (each one flips a number)

- **Έναντι vs εκκαθαριστικός:** a clearing bill (`εκκαθαριστικός`) nets out a prior on-account charge via a negative `Αξία Ρεύματος Έναντι` line. The printed payable is then LESS than the period's real cost — reconstruct the gross (add the έναντι back, plus its VAT) for a true comparison.
- **Carried debt:** `Προηγούμενο Ανεξόφλητο Ποσό` and final-payable include old arrears. Compare on the **current-period** charge, not final payable.
- **Night/dual tariff (Γ1Ν, διζωνικό):** has separate day (κανονική) and night (μειωμένη) registers. Don't apply a single flat offer rate to its total kWh — price each register, or note the ~25–30% night share. Few suppliers offer dual-zone (ΔΕΗ EnterTwo fixed, Zenith Go Electric Plus floating); ΗΡΩΝ does not.
- **Consumption level sets the lever:** at low kWh/month the **πάγιο (standing charge) dominates** → a zero-πάγιο plan usually wins even at a higher rate. At high kWh the energy rate dominates. Compute, don't assume.
- **Business/κοινόχρηστα supplies** (common areas, often ≥25 kVA) use business tariffs and higher ΕΦΚ (0,005) — residential offers don't apply. Confirm a candidate explicitly accepts a **shared κοινόχρηστα meter** before recommending it; the cheapest business product may not, and that caveat can decide the answer.
- **Don't compare floating vs fixed on price alone — they're different risk products.** A floating tariff can be cheaper *today* than a fixed one, but they answer different questions (track the market vs lock a price). Decide the strategy first (see step 6), rank *within* the tier, and weigh the fixed term's length. "Cheapest right now" across tiers is a misleading headline.
- **A short sample misses the seasons.** Greek consumption swings hard (summer A/C, winter heating). 6–8 bills can't reveal that, and **naively annualising a short sample** (×365/days) over- or under-weights whatever season you happened to capture. Use ≥12 consecutive months where possible, or weight by season, and always label the estimate's coverage and that it's not seasonally representative.
- **Tiered & formula-indexed tariffs aren't a single rate.** Many products are tiered (e.g. 0–700 / >700 kWh, day >200 kWh) or indexed (`a×DAM+b`, hourly MCP). Reduce them to an **effective** €/kWh at the supply's actual monthly kWh and the current wholesale index *before* feeding the engine — see `tiered_effective_rate` in [backtest_engine.py](backtest_engine.py).
- **Discounts are conditional** (έκπτωση συνέπειας/on-time, πάγια εντολή, e-bill). Headline rates assume you keep them; a missed payment reverts to a much higher nominal rate.
- **Floating rates reset monthly.** Verify any Κίτρινο/Πράσινο rate on the official ΡΑΑΕΥ tool **energycost.gr** before relying on it. Fixed (Μπλε) rates lock for the term.

## Deliverables that work

For a multi-supply comparison build an Excel workbook (openpyxl) with live formulas so rates can be tweaked: `Bills_Raw, Supplies, Bill_Line_Items, Fee_Model, Market_Offers, Scenario_Model, Backtest, Recommendation`. Validate the embedded formulas by a headless `soffice --headless --convert-to xlsx` recalc and reading values back with `data_only=True`.

## Red flags — stop and recompute

- Comparing on a headline `0,08xx €/kWh` without finding the Διακύμανση/ρήτρα line
- **Naming a "cheapest" provider from memory of the big names** instead of ranking the live energycost.gr list (the winner is often a non-incumbent)
- **Ranking floating vs 1-year-fixed vs 2-year-fixed in one flat list** (apples-to-oranges) — decide commit-vs-market first, then rank within tier
- **Ignoring contract length / lock-in** when recommending a fixed product (a 2-year lock in a volatile market is a cost, not free certainty)
- **Annualising a 6–8-bill sample by scaling** as if it were seasonally representative
- Recommending a product without confirming the **meter/segment fits** (κοινόχρηστα, kVA, dual-zone)
- Treating a **tiered or DAM/MCP-indexed** tariff as one flat rate
- Applying VAT to municipal fees or ΕΡΤ (it doesn't apply there)
- Using final-payable (includes arrears) instead of current-period cost
- Recommending a low-rate/high-πάγιο plan for a near-dormant supply
- Quoting a floating rate as if it were stable, or not checking energycost.gr
