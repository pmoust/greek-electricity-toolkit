#!/usr/bin/env python3
"""Generate SYNTHETIC (fictional) Greek-electricity demo data for the example
report and spreadsheet. No real customer data is used — names, addresses, supply
numbers and consumption are invented. Bills are constructed from the reference
fee model so each one reconciles to the cent, exactly like a real bill.

Outputs: example_bills.json  (same schema the workbook builder expects)
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

# --- regulated unit rates (public, mid-2026 reference) ---
TRANSMISSION = 0.01151   # ADMIE EUR/kWh
DISTRIB_KWH = 0.00339    # DEDDIE EUR/kWh
DISTRIB_KVA_RES = 6.21   # DEDDIE EUR/kVA-yr residential
DISTRIB_KVA_BUS = 11.339 # DEDDIE EUR/kVA-yr business
ETMEAR = 0.017
YKO_RES = 0.00699
EFK_RES = 0.0022
EFK_BUS = 0.005
VAT = 0.06
ERT_YEAR = 36.0

def r2(x): return round(x + 1e-9, 2)

def regulated(kwh, kva, days, business):
    tr = kwh * TRANSMISSION
    dist = kva * (DISTRIB_KVA_BUS if business else DISTRIB_KVA_RES) * days / 365 + kwh * DISTRIB_KWH
    etmear = kwh * ETMEAR
    yko = kwh * YKO_RES
    return r2(tr + dist + etmear + yko)

def build_bill(file, sid, provider, product, p_start, p_end, days, issue,
               kwh_day, kwh_night, day_rate, night_rate, paygio, kva,
               municipal, business, ert=True):
    kwh = kwh_day + kwh_night
    energy = kwh_day * day_rate + (kwh_night * night_rate if night_rate else 0)
    A = r2(paygio + energy)
    B = regulated(kwh, kva, days, business)
    efk = r2(kwh * (EFK_BUS if business else EFK_RES))
    special = r2(0.005 * energy)
    G = r2(efk + special)
    E = r2(municipal)
    ST = r2(ERT_YEAR * days / 365) if ert else 0.0
    vat_base = r2(A + B + efk)
    vat = r2(VAT * vat_base)
    total = r2(A + B + G + E + ST + vat)
    return {
        "file": file, "supply_id": sid, "provider": provider, "product": product,
        "type": "clearing", "period_start": p_start, "period_end": p_end, "days": days,
        "issue": issue, "kwh_total": kwh, "kwh_day": kwh_day, "kwh_night": kwh_night,
        "energy_day_rate": day_rate, "energy_base_rate": day_rate,
        "energy_night_rate": night_rate, "adj_rate": None,
        "loyalty_disc_pct": 0, "ena_disc": 0, "fixed_paygio": paygio,
        "A_supply": A, "B_regulated": B, "G_supplementary": G,
        "efk": efk, "special5permille": special, "late_interest": 0.0,
        "E_municipal": E, "ST_ert": ST, "vat": vat, "vat_base": vat_base,
        "enanti_credit": 0.0, "prev_unpaid": 0.0,
        "current_total": total, "final_payable": total,
    }

supplies = [
    {"id":"D1","provider":"Provider-A","supply_no":"0-00000000-0","property":"DEMO — Main residence (night tariff)",
     "customer_type":"residential","product":"Night Floating (demo)","tariff_type":"floating night",
     "power_kva":35,"phases":3,"register":"dual (day/night)","priority":"HIGH","efk_per_kwh":EFK_RES,
     "notes":"Synthetic. High consumption ~950 kWh/mo, ~30% on night register."},
    {"id":"D2","provider":"Provider-B","supply_no":"0-00000000-1","property":"DEMO — Apartment",
     "customer_type":"residential","product":"Home Floating (demo)","tariff_type":"floating",
     "power_kva":8,"phases":1,"register":"single","priority":"medium","efk_per_kwh":EFK_RES,
     "notes":"Synthetic. ~280 kWh/mo single-register."},
    {"id":"D3","provider":"Provider-B","supply_no":"0-00000000-2","property":"DEMO — Building common areas",
     "customer_type":"business","product":"Business Floating (demo)","tariff_type":"floating business",
     "power_kva":25,"phases":3,"register":"single","priority":"medium","efk_per_kwh":EFK_BUS,
     "notes":"Synthetic. Common areas (koinochrista), 25 kVA, ~700 kWh/mo."},
]

bills = [
    # D1 night residence — floating effective ~0.155 day / 0.123 night
    build_bill("demo_d1_apr","D1","Provider-A","Night Floating (demo)","2026-04-01","2026-04-30",30,"2026-05-18",
               700,250,0.155,0.123,5.00,35,46.0,False),
    build_bill("demo_d1_may","D1","Provider-A","Night Floating (demo)","2026-05-01","2026-05-31",31,"2026-06-18",
               740,260,0.155,0.123,5.00,35,47.5,False),
    # D2 apartment — floating ~0.157
    build_bill("demo_d2_apr","D2","Provider-B","Home Floating (demo)","2026-04-01","2026-04-30",30,"2026-05-20",
               285,0,0.157,None,5.50,8,5.0,False),
    build_bill("demo_d2_may","D2","Provider-B","Home Floating (demo)","2026-05-01","2026-05-31",31,"2026-06-20",
               300,0,0.157,None,5.50,8,5.2,False),
    # D3 common areas business — floating ~0.168
    build_bill("demo_d3_apr","D3","Provider-B","Business Floating (demo)","2026-04-01","2026-04-30",30,"2026-05-22",
               680,0,0.168,None,5.50,25,2.0,True,ert=False),
    build_bill("demo_d3_may","D3","Provider-B","Business Floating (demo)","2026-05-01","2026-05-31",31,"2026-06-22",
               720,0,0.168,None,5.50,25,2.1,True,ert=False),
]

data = {
    "meta": {"analysis_date":"2026-06-24","vat_rate":VAT,
             "efk_residential_per_kwh":EFK_RES,"efk_business_per_kwh":EFK_BUS,
             "notes":"SYNTHETIC DEMO DATA — fictional supplies, no real customer. "
                     "VAT(6%) base = A + B + EFK. Regulated/municipal/ERT/taxes are provider-independent; only A changes on a switch."},
    "supplies": supplies, "bills": bills,
}

# sanity: every bill reconciles
for b in bills:
    s = r2(b["A_supply"]+b["B_regulated"]+b["G_supplementary"]+b["E_municipal"]+b["ST_ert"]+b["vat"])
    assert abs(s - b["current_total"]) < 0.005, (b["file"], s, b["current_total"])
    assert abs(b["vat"] - r2(VAT*b["vat_base"])) < 0.005, b["file"]

json.dump(data, open(os.path.join(HERE,"example_bills.json"),"w"), ensure_ascii=False, indent=2)
print("wrote example_bills.json —", len(bills), "synthetic bills, all reconcile.")
