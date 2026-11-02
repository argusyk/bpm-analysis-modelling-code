# -*- coding: utf-8 -*-
"""Generator of a synthetic event log of AeroCargo's "as-is" process.
The parameters are consistent with Table 6.1 of the book (mean waits and durations,
29 % document rework, peak waiting for screening, 7 % of shipments
with a customs request before screening is completed). The parallel_share metric in
pm_analysis.py counts only shipments whose release came before screening (~3 %), see Section 6.8.3.
Run: python generate_log.py [number_of_shipments]  ->  aerocargo_export_log.csv"""
import csv, os, random, sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
random.seed(2026)
T0 = datetime(2026, 3, 2, 0, 0)

def awb():
    serial = random.randint(1_000_000, 9_999_999)
    return f"176-{serial}{serial % 7}"          # check digit according to the IATA rule

def work(mean):                                  # work duration: gamma with k = 4
    return random.gammavariate(4, mean / 4)

def wait(mean):                                  # waiting: exponential distribution
    return random.expovariate(1 / mean)

def arrival_hour():                              # peak profile of cargo deliveries
    return random.choices(range(24), weights=[1,1,1,1,1,2,4,6,9,12,12,9,7,6,5,5,4,3,3,2,2,1,1,1])[0]

rows = []
for i in range(N):
    case = awb()
    day = i * 24 / 80                             # ~80 shipments per day
    t = T0 + timedelta(hours=int(day // 24) * 24 + arrival_hour() + random.random())
    ev = lambda act, when, res: rows.append((case, act, when.strftime("%Y-%m-%d %H:%M:%S"), res))
    ev("Confirm booking", t - timedelta(hours=random.uniform(12, 60)), "commercial department")
    ev("Cargo delivered", t, "warehouse")
    t += timedelta(hours=wait(0.50) + work(0.35)); ev("Accept cargo", t, f"storekeeper {random.randint(1, 9):02d}")
    t += timedelta(hours=wait(1.28) + work(0.15)); ev("Check e-AWB data", t, f"agent {random.randint(1, 4):02d}")
    while random.random() < 0.29:                # document correction loop
        t += timedelta(hours=0.03); ev("Request correction", t, "documentation service")
        if random.random() < 0.07:
            t += timedelta(hours=4); ev("Escalate to shift supervisor", t, "shift supervisor")
        t += timedelta(hours=wait(1.0)); ev("Receive correction", t, "freight forwarder")
        t += timedelta(hours=work(0.15)); ev("Check e-AWB data", t, f"agent {random.randint(1, 4):02d}")
    parallel = random.random() < 0.07            # informal practice: customs in parallel
    peak = 10 <= t.hour < 12
    t_screen = t + timedelta(hours=wait(3.0 if peak else 0.9) + work(0.25))
    if random.random() < 0.035:
        ev("Pass screening", t_screen, "AvSec")
        t_screen += timedelta(hours=work(1.0)); ev("Repack", t_screen, f"storekeeper {random.randint(1, 9):02d}")
        t_screen += timedelta(hours=wait(0.5) + work(0.25))
    if parallel:
        t_cust = t + timedelta(hours=wait(1.0) + work(0.2))
        ev("Obtain customs release", t_cust, "customs post")
        ev("Pass screening", t_screen, "AvSec")
        t = max(t_cust, t_screen)
    else:
        ev("Pass screening", t_screen, "AvSec")
        t = t_screen + timedelta(hours=wait(1.0) + work(0.2)); ev("Obtain customs release", t, "customs post")
    t += timedelta(hours=wait(0.5) + work(0.3)); ev("Hand over ULD", t, "ULD team")

rows.sort(key=lambda r: (r[2], r[0]))
out = os.path.join(HERE, "aerocargo_export_log.csv")
with open(out, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["case_id", "activity", "timestamp", "resource"])
    w.writerows(rows)
print(f"saved {out}: {N} shipments, {len(rows)} events")
