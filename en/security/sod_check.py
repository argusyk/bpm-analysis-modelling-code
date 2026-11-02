# -*- coding: utf-8 -*-
"""Segregation of Duties (SoD) check against an event log.
The rules specify pairs of activities that one person may not perform within one case.
For demonstration, a purchasing process log with several violations is generated.
Run: python sod_check.py  (results -> results.json)"""
import csv, json, os, random
from collections import Counter, defaultdict
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = [("Create purchase requisition", "Approve purchase requisition"),
         ("Approve purchase requisition", "Confirm receipt of goods"),
         ("Confirm receipt of goods", "Approve invoice payment"),
         ("Create purchase requisition", "Approve invoice payment")]
STEPS = ["Create purchase requisition", "Approve purchase requisition", "Confirm receipt of goods",
         "Approve invoice payment"]
POOL_REDESIGNED = {"Create purchase requisition": ["requester_01", "requester_02", "requester_03"],
        "Approve purchase requisition": ["manager_01", "manager_02"],
        "Confirm receipt of goods": ["storekeeper_01", "storekeeper_02"],
        "Approve invoice payment": ["finance_01", "finance_02"]}
POOL = {"Create purchase requisition": ["requester_01", "requester_02", "requester_03", "manager_01"],
        "Approve purchase requisition": ["manager_01", "manager_02"],
        "Confirm receipt of goods": ["storekeeper_01", "storekeeper_02", "manager_02"],
        "Approve invoice payment": ["finance_01", "finance_02"]}


def generate(path, n=500, seed=7, pool=None):
    pool = pool or POOL
    random.seed(seed)
    t0 = datetime(2026, 4, 1, 9)
    rows = []
    for i in range(n):
        case, t = f"PR-{1000 + i}", t0 + timedelta(hours=i * 3)
        who = {}
        for s in STEPS:
            who[s] = random.choice(pool[s])
        if random.random() < 0.03:                       # "approved own requisition"
            who["Approve purchase requisition"] = who["Create purchase requisition"] = "manager_01"
        if random.random() < 0.02:                       # approved and received the goods themselves
            who["Confirm receipt of goods"] = who["Approve purchase requisition"] = "manager_02"
        for s in STEPS:
            t += timedelta(hours=random.uniform(2, 30))
            rows.append((case, s, t.strftime("%Y-%m-%d %H:%M:%S"), who[s]))
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";"); w.writerow(["case_id", "activity", "timestamp", "resource"]); w.writerows(rows)


def check(path):
    by_case = defaultdict(dict)
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            by_case[r["case_id"]].setdefault(r["activity"], set()).add(r["resource"])
    violations = []
    for case, acts in by_case.items():
        for a, b in RULES:
            common = acts.get(a, set()) & acts.get(b, set())
            for person in common:
                violations.append((case, a, b, person))
    return by_case, violations


if __name__ == "__main__":
    R = {}
    for name, pool in (("current roles", POOL), ("redesigned roles", POOL_REDESIGNED)):
        log = os.path.join(HERE, "procurement_log.csv" if pool is POOL else "procurement_log_redesigned.csv")
        generate(log, pool=pool)
        cases, v = check(log)
        R[name] = {"cases": len(cases), "violations": len(v), "cases_with_violation": len({x[0] for x in v}),
                   "violation_rate": round(len({x[0] for x in v}) / len(cases), 3),
                   "by_rule": Counter(f"{a} / {b}" for _, a, b, _ in v), "by_person": Counter(p for *_, p in v)}
        r = R[name]
        print(f"[{name}] cases: {r['cases']}, violations: {r['violations']}, cases with violations: {r['cases_with_violation']} ({r['violation_rate']:.1%})")
        for k, n in r["by_rule"].items(): print(f"    rule \"{k}\": {n}")
        for k, n in r["by_person"].items(): print(f"    performer {k}: {n}")
    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as _f:
        json.dump(R, _f, ensure_ascii=False, indent=1)