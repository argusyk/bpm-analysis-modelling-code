# -*- coding: utf-8 -*-
"""Контрольна карта середніх (X-bar, S) для часу обробки відправок (розділ 7.10).
Відправки впорядковуються за часом доставки і групуються по n = 25 поспіль;
для кожної підгрупи обчислюється середнє і стандартне відхилення часу обробки.
Межі: UCL/LCL = x̿ ± A3·s̄ (для n = 25 A3 = 0,606). Перевіряються правила:
точка поза межами; 8 точок поспіль з одного боку від центральної лінії.
Запуск: python spc_chart.py  (результати -> spc_results.json)"""
import json, os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
N, A3 = 25, 0.606

df = pd.read_csv(os.path.join(HERE, "..", "data", "aerocargo_export_log.csv"), sep=";", encoding="utf-8-sig",
                 parse_dates=["timestamp"])
start = df[df.activity == "Вантаж доставлено"].groupby("case_id").timestamp.min()
end = df[df.activity == "Передати ULD"].groupby("case_id").timestamp.max()
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
print(f"підгруп: {k} по {N} відправок, центральна лінія {xbb:.2f} год, s̄ = {sbar:.2f}")
print(f"UCL = {ucl:.2f} год, LCL = {lcl:.2f} год")
print("точки поза межами:", out or "немає")
print("серії з 8 точок з одного боку (кінець серії):", runs or "немає")
