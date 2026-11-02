# -*- coding: utf-8 -*-
"""Activity-based costing (ABC) of AeroCargo's export shipment handling process.
Resources -> activities (by resource drivers) -> cost objects (by activity drivers).
Compared with the traditional allocation of overheads in proportion to weight.
Run: python abc_costing.py  (results -> results.json)"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))

# 1. Monthly resource costs, c.u.
# (consistent with Table 3.4: ~38 c.u. per tonne of export cargo)
resources = {"Warehouse staff": 5700, "Documentation service": 2450, "Screening line": 2050,
             "Forklifts and ramp": 1640, "IT systems": 1224}
# 2. Resource drivers: the shares of a resource consumed by each activity
consumption = {
    "Warehouse staff":       {"Cargo acceptance": 0.55, "ULD build-up": 0.35, "Special cargo handling": 0.10},
    "Documentation service":   {"Document checking": 0.60, "Document correction": 0.25, "Customs clearance": 0.15},
    "Screening line":       {"Screening": 1.00},
    "Forklifts and ramp": {"Cargo acceptance": 0.40, "ULD build-up": 0.60},
    "IT systems":            {"Document checking": 0.40, "Customs clearance": 0.30, "Cargo acceptance": 0.30}}
# 3. Cost objects: consumption of activity drivers per shipment and monthly volume
objects = {  # per shipment
    "Standard shipment (5 pieces, 150 kg)": {"Cargo acceptance": 5, "ULD build-up": 0.17, "Document checking": 1.2,
                                               "Document correction": 0.25, "Customs clearance": 1, "Screening": 0.2},
    "Dangerous goods (2 pieces, 60 kg)": {"Cargo acceptance": 2, "ULD build-up": 0.5, "Special cargo handling": 1,
                                            "Document checking": 3, "Document correction": 0.8, "Customs clearance": 1,
                                            "Screening": 0.6}}
volume = {"Standard shipment (5 pieces, 150 kg)": 2220, "Dangerous goods (2 pieces, 60 kg)": 180}
weights = {"Standard shipment (5 pieces, 150 kg)": 150, "Dangerous goods (2 pieces, 60 kg)": 60}
UNITS = {"Cargo acceptance": "cargo pieces", "ULD build-up": "ULD", "Special cargo handling": "special shipments",
         "Document checking": "checks", "Document correction": "corrections",
         "Customs clearance": "declarations", "Screening": "screening hours"}
# activity driver volumes are derived from the mix, so the allocation is always consistent
drivers = {a: (UNITS[a], sum(objects[o].get(a, 0) * volume[o] for o in objects)) for a in UNITS}
monthly_kg = sum(weights[o] * volume[o] for o in objects)

activity_cost = {}
for res, shares in consumption.items():
    for act, s in shares.items():
        activity_cost[act] = activity_cost.get(act, 0) + resources[res] * s
rate = {a: activity_cost[a] / drivers[a][1] for a in activity_cost}
abc = {o: round(sum(rate[a] * q for a, q in use.items()), 2) for o, use in objects.items()}
total = sum(resources.values())
traditional = {o: round(total / monthly_kg * w, 2) for o, w in weights.items()}
per_tonne = round(total / monthly_kg * 1000, 1)
check = round(sum(abc[o] * volume[o] for o in objects))
R = {"resources_total": total, "cost_per_tonne": per_tonne, "reconciled_total": check, "volume": volume, "drivers": {a: [round(v[1], 1), v[0]] for a, v in drivers.items()}, "activity_cost": {a: round(v) for a, v in activity_cost.items()},
     "driver_rate": {a: [round(rate[a], 2), drivers[a][0]] for a in rate}, "abc_cost": abc, "traditional_cost": traditional}
with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as _f:
    json.dump(R, _f, ensure_ascii=False, indent=1)
print("activity costs:", R["activity_cost"])
print("driver rates:", R["driver_rate"])
print("driver volumes:", {a: round(v[1],1) for a, v in drivers.items()}); print("reconciliation: sum over objects =", check, "of", total); print("cost per tonne:", per_tonne); print("ABC:", abc); print("traditional (by weight):", traditional)
