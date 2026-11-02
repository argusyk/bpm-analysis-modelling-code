# -*- coding: utf-8 -*-
"""Control chart of means (X-bar, S) for shipment handling time (Section 7.10).
Shipments are ordered by delivery time and grouped into consecutive subgroups of n = 25;
for each subgroup the mean and standard deviation of handling time are calculated.
Limits: UCL/LCL = x̿ ± A3·s̄ (for n = 25, A3 = 0.606). The rules checked are:
a point outside the limits; 8 consecutive points on one side of the centre line.
Run: python spc_chart.py  (results -> spc_results.json)"""
import json, os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
N, A3 = 25, 0.606

df = pd.read_csv(os.path.join(HERE, "..", "data", "aerocargo_export_log.csv"), sep=";", encoding="utf-8-sig",
                 parse_dates=["timestamp"])
start = df[df.activity == "Cargo delivered"].groupby("case_id").timestamp.min()
end = df[df.activity == "Hand over ULD"].groupby("case_id").timestamp.max()
ct = ((end - start).dt.total_seconds() / 3600).dropna()
order = start.loc[ct.index].sort_values().index
ct = ct.loc[order].reset_index(drop=True)
k = len(ct) // N
groups = [ct.iloc[i * N:(i + 1) * N] for i in range(k)]
xbar = [g.mean() for g in groups]
s = [g.std(ddof=1) for g in groups]
xbb, sbar = sum(xbar) / k, sum(s) / k
ucl, lcl = xbb + A3 * sbar, max(0.0, xbb - A3 * sbar)
out = [i + 1 for i, x in enumerate(xbar) if x > ucl or x < lcl]
runs, side, cnt = [], 0, 0
for i, x in enumerate(xbar):
    sd = 1 if x > xbb else -1
    cnt = cnt + 1 if sd == side else 1
    side = sd
    if cnt == 8:
        runs.append(i + 1)
R = {"n": N, "subgroups": k, "center": round(xbb, 2), "s_bar": round(sbar, 2), "UCL": round(ucl, 2), "LCL": round(lcl, 2),
     "xbar": [round(x, 2) for x in xbar], "out_of_limits": out, "runs_of_8_end": runs,
     "period": [str(start.min())[:10], str(start.max())[:10]]}
with open(os.path.join(HERE, "spc_results.json"), "w", encoding="utf-8") as _f:
    json.dump(R, _f, ensure_ascii=False, indent=1)
print(f"subgroups: {k} of {N} shipments, centre line {xbb:.2f} h, s_bar = {sbar:.2f}")
print(f"UCL = {ucl:.2f} h, LCL = {lcl:.2f} h")
print("points outside the limits:", out or "none")
print("runs of 8 points on one side (end of run):", runs or "none")
