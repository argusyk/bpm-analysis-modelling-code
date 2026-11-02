# -*- coding: utf-8 -*-
"""Process mining of real Prozorro open tenders: variants, stage durations,
the impact of complaints and rejections, the directly-follows graph.
Run: python analyze.py  (results -> results.json)"""
import os, json, warnings
warnings.filterwarnings("ignore")
import pandas as pd
import pm4py

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, "prozorro_log.csv"), sep=";", encoding="utf-8-sig", parse_dates=["timestamp"])
tn = pd.read_csv(os.path.join(HERE, "prozorro_tenders.csv"), sep=";", encoding="utf-8-sig")
log = pm4py.format_dataframe(df, case_id="case_id", activity_key="activity", timestamp_key="timestamp")
R = {"cases": int(df.case_id.nunique()), "events": int(len(df))}
R["status"] = tn.status.value_counts().to_dict()

var = pm4py.get_variants(log)
cnt = sorted(((v if isinstance(v, int) else len(v)), k) for k, v in var.items())[::-1]
R["variants"] = len(var)
R["top_variants"] = [[" > ".join(k), n] for n, k in cnt[:3]]

first = df.groupby("case_id").timestamp.min()
days = lambda a, b: (b - a).dt.total_seconds() / 86400
piv = df.pivot_table(index="case_id", columns="activity", values="timestamp", aggfunc="min")
contract = df[df.activity == "Contract signed"].groupby("case_id").timestamp.min()
dur = days(first[contract.index], contract)
R["days_to_contract"] = {"median": round(dur.median(), 1), "mean": round(dur.mean(), 1), "p90": round(dur.quantile(0.9), 1)}

def stage(a, b):
    x = days(piv[a], piv[b]).dropna()
    x = x[x >= 0]
    return round(x.median(), 1)
R["stage_median_days"] = {
    "announcement -> bid deadline": stage("Tender announced", "Bid submission deadline"),
    "bid deadline -> auction": stage("Bid submission deadline", "Auction held"),
    "auction -> winner": stage("Auction held", "Winner awarded"),
    "winner -> contract": stage("Winner awarded", "Contract signed")}

acts = df.groupby("case_id").activity.apply(set)
has = lambda a: acts.apply(lambda s: a in s)
R["share_auction"] = round(has("Auction held").mean(), 3)
R["share_complaint"] = round(has("Complaint submitted").mean(), 3)
R["share_rejection"] = round(has("Bid rejected").mean(), 3)
comp = has("Complaint submitted"); rej = has("Bid rejected")
idx = dur.index
R["median_days_with_complaint"] = round(dur[comp[idx]].median(), 1) if comp[idx].any() else None
R["median_days_without_complaint"] = round(dur[~comp[idx]].median(), 1)
R["median_days_with_rejection"] = round(dur[rej[idx]].median(), 1)
R["median_days_without_rejection"] = round(dur[~rej[idx]].median(), 1)
R["bids"] = tn.bids.value_counts().sort_index().to_dict()
R["median_bids"] = float(tn.bids.median())
R["single_bid_share"] = round((tn.bids == 1).mean(), 3)

dfg, s, e = pm4py.discover_dfg(log)
R["dfg"] = [[a, b, int(n)] for (a, b), n in sorted(dfg.items(), key=lambda x: -x[1])[:14]]
R["dur_hist_days"] = [int(((dur >= a) & (dur < a + 7)).sum()) for a in range(0, 84, 7)]

with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as _f:

    json.dump(R, _f, ensure_ascii=False, indent=1, default=str)
for k, v in R.items():
    if k not in ("dfg", "dur_hist_days"): print(f"{k}: {v}")
print("DFG:"); [print("  ", a, "->", b, n) for a, b, n in R["dfg"]]
