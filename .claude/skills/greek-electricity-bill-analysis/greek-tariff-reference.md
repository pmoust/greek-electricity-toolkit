# Greek Electricity Tariff Reference

Snapshot researched **2026-06**. Floating rates reset monthly — re-verify on the official ΡΑΑΕΥ comparison tool **energycost.gr** (also invoices.rae.gr/oikiako) before relying on any Κίτρινο/Πράσινο figure. Fixed (Μπλε) rates lock for the term.

## RAAEY tariff colors (standardised since 1.1.2024, N.4986/2022)

| Color | Structure | Adjustment clause (ρήτρα) | Price known | Notes |
|---|---|---|---|---|
| **Μπλε / Blue** | **Fixed** for the term (≥12 mo) | **None** | before signing | the certainty choice |
| **Πράσινο / Green** | special, re-set on the 1st of each month | folded into the monthly price | start of month | the regulator's benchmark product |
| **Κίτρινο / Yellow** | floating, indexed to wholesale | **explicit, separate `Διακύμανση Κόστους Αγοράς` line** | after the month | where most "cheap headline" products sit |
| **Πορτοκαλί / Orange** | dynamic hourly (needs smart meter) | real-time | day before | households since 1.4.2026 |

**Provider marketing names don't always match the regulatory color** — verify the mechanism (is there an adjustment line?), not the brand label.

## Strategy before price (don't compare across tiers)

Floating, 1-year fixed and 2-year fixed are **different products on a risk axis**, not rival price points — ranking them in one list is apples-to-oranges. The decision order is:

1. **Commit to a price or follow the market?** Fixed (Μπλε) locks a rate and removes monthly-reset risk; floating (Κίτρινο/Πράσινο) tracks wholesale and can be cheaper now but moves.
2. **If fixed, for how long?** A multi-year lock (e.g. a 24-month tariff) is only "cheaper" if you'd actually hold it. In a volatile market (fuel/geopolitical shocks) a long lock carries opportunity risk if prices fall — and an early-exit fee if you leave. Treat **term length** as a first-class factor, not a footnote.
3. **Then** rank cheapest-within-tier and compare the cheapest *floating* vs cheapest *1y-fixed* vs cheapest *2y-fixed* as three distinct choices.

**Sample & seasonality:** a handful of bills (e.g. 6–8) can't show seasonal swings (summer A/C, winter heating). Don't annualise a short sample by naive scaling — it over/under-weights the season you captured. Use ≥12 consecutive months, or weight by season, and label coverage.

## Charge basis & who sets it

| Line | Who | Basis | Changes w/ supplier | In VAT base |
|---|---|---|---|---|
| Πάγιο (standing charge) | supplier | €/month (prorated by days) | YES | yes |
| Energy χρέωση | supplier | €/kWh (× day/night) | YES | yes |
| Διακύμανση Κόστους Αγοράς / ρήτρα | supplier | €/kWh | YES | yes |
| Εκπτώσεις (συνέπειας/e-bill/παγ.εντολή/παραμονής) | supplier | % or €/kWh | YES | reduce base |
| ΑΔΜΗΕ – Σύστημα Μεταφοράς (transmission) | regulated | €/kWh (+€/kVA) | NO | yes |
| ΔΕΔΔΗΕ – Δίκτυο Διανομής (distribution) | regulated | €/kVA·yr + €/kWh | NO | yes |
| ΕΤΜΕΑΡ (RES levy) | regulated | €/kWh | NO | yes |
| ΥΚΩ (public service obligations) | regulated | tiered €/kWh (+night band) | NO | yes |
| ΕΦΚ (excise) | state | €/kWh | NO | **yes** |
| Ειδικό Τέλος 5‰ (N.2093/92) | state | 0.5% of energy value | NO | **no** |
| Δημοτικά Τέλη/Φόρος (ΔΤ/ΔΦ) | municipality | €/m² × days | NO | **no** |
| ΤΑΠ | municipality | €/m² × zone × age × days | NO | **no** |
| ΕΡΤ | ERT | 36 €/yr prorated | NO | **no** |

## Verified unit values (mid-2026)

- **VAT (ΦΠΑ):** 6% (reduced for electricity). Base = `Προμήθεια(A) + Ρυθμιζόμενες(B) + ΕΦΚ`. NOT on municipal/ΕΡΤ/5‰/interest.
- **ΕΦΚ:** **0,0022 €/kWh residential**, **0,005 €/kWh business** (confirm on the bill: ΕΦΚ ÷ kWh).
- **ΕΤΜΕΑΡ:** 0,017 €/kWh.
- **ΑΔΜΗΕ transmission:** ~0,01151 €/kWh (eff. 1.2.2026).
- **ΔΕΔΔΗΕ distribution capacity:** ~6,21 €/kVA·yr residential, ~11,339 €/kVA·yr for 25 kVA business; + ~0,00339 €/kWh.
- **ΥΚΩ (residential, per 4-month band):** 0,00699 (0–1600 kWh) / 0,05 (1601–2000) / 0,085 (>2000) €/kWh; reduced ~0,0069 on the night register.

## Night / dual-zone (Γ1Ν, διζωνικό)

Day (κανονική) and night (μειωμένη) registers. National night windows: **winter (1 Nov–31 Mar)** 02:00–05:00 + 12:00–15:00; **summer (1 Apr–31 Oct)** 02:00–04:00 + 11:00–15:00; weekends/holidays reduced all day. Dual-zone supply products are scarce: **ΔΕΗ myHome EnterTwo** (fixed), **Zenith Power Home Go Electric Plus** (floating). ΗΡΩΝ has no residential dual-zone supply product.

## Suppliers to check (mid-2026) — and the traps

**Always pull the live list from energycost.gr** before relying on this; the market consolidates fast. Check every ACTIVE supplier (don't reason from the big names only — the cheapest is often a non-incumbent). Account for who has merged, gone direct-only, or exited.

| Supplier | Status | Notes for comparison |
|---|---|---|
| ΔΕΗ / PPC | active, incumbent | only mainstream dual-zone Γ1Ν fixed (myHome EnterTwo) |
| ΗΡΩΝ / Heron | active | PROTECT = floating w/ Διακύμανση; Generous/Yellow families cheaper |
| Protergia (Metlen) | active | absorbed **WATT+VOLT** and **EFA Energy** |
| Elpedison → **Enerwave** | active (rebranded) | HELLENiQ Energy; use enerwave.gr |
| NRG (Motor Oil) | active | aggregator-sourced rates; removed e-bill/direct-debit discounts 01.03.2026 |
| Φυσικό Αέριο Ελλ. Εταιρεία Ενέργειας | active | site often blocks scraping; some tiered products |
| Volton | active | ΜΤΑΜ-indexed floating products |
| Zenith (Eni) | active | offers dual-zone (Go Electric Plus) |
| ELIN / ELINOIL | active | low-/zero-πάγιο; cheap business green (κοινόχρηστα acceptance to confirm) |
| WE Energy / Eunice Power | active | weenergy.gr → eunice-power.gr; formula-indexed (DAM/MCP) products |
| ΟΤΕ Estate | active | single green/special product |
| Nova Energy (United Group) | active, **direct/in-store only** | not on aggregators; quote via energycost.gr / provider |
| PetroGaz Energy | active, **direct only** | no public per-kWh data |
| **Volterra** | **acquired by Metlen (Jul-2024)** | off switching platforms, pricing stale → treat as unavailable |
| **WATT+VOLT** | **defunct** → Protergia | not an independent option |
| **EFA Energy** | **merged** → Protergia | not an independent option |
| **ΕΛΤΑ Ενέργεια** | **exited electricity (2023)** | gone |
| **ΒΙΕΝΕΡ / Viener** | commercial/wholesale only | not a household option |
| **Octopus Energy** | **not in the Greek market** | — |

Provider marketing names don't always match the RAAEY color — verify the mechanism, not the brand.

## Regulated extras & policy items

- **Government subsidy "Τ.Ε.Μ." (Ταμείο Ενεργειακής Μετάβασης):** per-kWh credit applied to all suppliers *only when activated*. Model as **0** unless a specific month's subsidy is announced; if active it appears as a separate credit line.
- **ΚΟΤ (Κοινωνικό Οικιακό Τιμολόγιο)** social tariff and **heating allowance**: eligibility-based, provider-independent — they don't differentiate suppliers in a comparison.
- **VAT and ΕΦΚ are policy-set and change.** The 6% electricity VAT and the 0,0022 €/kWh residential ΕΦΚ are reduced/crisis-era values — re-verify they're still current.

## Reading-a-bill cheatsheet

- `Εκκαθαριστικός` = clearing/settlement bill; `Έναντι` = on-account/estimated. A clearing bill may carry a negative `Αξία Ρεύματος Έναντι` that nets out a prior έναντι charge — the printed payable is then below the period's true cost.
- `Προηγούμενο Ανεξόφλητο Ποσό` = carried debt; excluded from current-period comparison.
- ΗΡΩΝ `Έκπτωση Ποσότητας (Παραμονής)` = quantity/loyalty discount; `Έκπτωση ΕΝ.Α` = a product credit line — include it or the bill won't reconcile.
- Effective ΗΡΩΝ PROTECT rate ≈ `base 0,0825/0,0925 + Διακύμανση 0,07–0,09 − 5%` ≈ 0,15–0,18 €/kWh. The headline alone understates it by ~2×.
