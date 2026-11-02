# -*- coding: utf-8 -*-
"""Object-centric event log (OCEL 2.0) of a purchasing process (Section 9.1.5).
Objects of four types: requisition, order, delivery, invoice. One event can
concern several objects: "Match invoice" links an invoice, one or two
orders and all their deliveries. The program builds the log, saves it in the
OCEL 2.0 format (JSON), discovers the object-centric graph (OC-DFG) and shows the distortions
caused by "flattening" the log into the classic form with a single case identifier.
Run: python build_ocel.py  (-> procurement.jsonocel, results.json)"""
import json, os, random, warnings
from datetime import datetime, timedelta
import pandas as pd
import pm4py
from pm4py.objects.ocel.obj import OCEL
warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
random.seed(11)
ev, rel, objs = [], [], []
t0 = datetime(2026, 5, 4, 9)


def event(act, t, links):
    eid = f"e{len(ev) + 1}"
    ev.append({"ocel:eid": eid, "ocel:activity": act, "ocel:timestamp": t})
    for oid, ot in links:
        rel.append({"ocel:eid": eid, "ocel:activity": act, "ocel:timestamp": t, "ocel:oid": oid, "ocel:type": ot,
                    "ocel:qualifier": ""})


def obj(oid, ot):
    objs.append({"ocel:oid": oid, "ocel:type": ot}); return (oid, ot)


pending = []                     # orders waiting for an invoice: (po, [deliveries], time)
for i in range(300):
    t = t0 + timedelta(hours=i * 2.5)
    rq = obj(f"RQ-{i + 1:04d}", "requisition")
    event("Create requisition", t, [rq])
    t += timedelta(hours=random.uniform(2, 20))
    event("Approve requisition", t, [rq])
    if random.random() < 0.05:                       # rejected requisitions
        continue
    t += timedelta(hours=random.uniform(1, 8))
    po = obj(f"PO-{i + 1:04d}", "order")
    event("Create order", t, [rq, po])
    dels = []
    for k in range(2 if random.random() < 0.3 else 1):   # 30 % of orders – in partial deliveries
        t += timedelta(hours=random.uniform(24, 96))
        d = obj(f"DL-{i + 1:04d}-{k + 1}", "delivery")
        event("Receive delivery", t, [po, d]); dels.append(d)
    pending.append((po, dels, t))
    # 20 % of invoices are issued by the supplier as one document for two orders
    if len(pending) == 2 or (len(pending) == 1 and random.random() > 0.2):
        tt = max(x[2] for x in pending) + timedelta(hours=random.uniform(4, 48))
        inv = obj(f"INV-{i + 1:04d}", "invoice")
        pos = [x[0] for x in pending]; ds = [d for x in pending for d in x[1]]
        event("Receive invoice", tt, [inv] + pos)
        tt += timedelta(hours=random.uniform(2, 30))
        event("Match invoice", tt, [inv] + pos + ds)
        tt += timedelta(hours=random.uniform(24, 120))
        event("Pay invoice", tt, [inv])
        pending = []

ocel = OCEL(events=pd.DataFrame(ev), objects=pd.DataFrame(objs), relations=pd.DataFrame(rel))
pm4py.write_ocel2_json(ocel, os.path.join(HERE, "procurement.jsonocel"))

R = {"events": len(ev), "objects": pd.DataFrame(objs)["ocel:type"].value_counts().to_dict(), "relations": len(rel)}
# flattening: how many events each classic log gets and how many of them are copies
R["flattening"] = {}
for ot in ["requisition", "order", "delivery", "invoice"]:
    flat = pm4py.ocel_flattening(ocel, ot)
    n = len(flat); uniq = flat["ocel:eid"].nunique() if "ocel:eid" in flat.columns else None
    acts = sorted(flat["concept:name"].unique())
    R["flattening"][ot] = {"rows": n, "unique_events": uniq, "activities": len(acts)}
# number of "Match invoice" events that concern several orders
multi = pd.DataFrame(rel).query("`ocel:activity` == 'Match invoice' and `ocel:type` == 'order'").groupby("ocel:eid").size()
R["match_events"] = int(len(multi)); R["match_events_two_orders"] = int((multi > 1).sum())
ocdfg = pm4py.discover_ocdfg(ocel)
R["ocdfg_edges"] = {ot: {f"{a} -> {b}": len(v) for (a, b), v in e.items()}
                    for ot, e in ocdfg["edges"]["event_couples"].items()}
with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as _f:
    json.dump(R, _f, ensure_ascii=False, indent=1)
print("events:", R["events"], "objects:", R["objects"], "event-object links:", R["relations"])
print("matching events:", R["match_events"], "of them for two orders:", R["match_events_two_orders"])
for ot, v in R["flattening"].items():
    print(f"flattening by type \"{ot}\": rows {v['rows']}, unique events {v['unique_events']}, activities {v['activities']}")
for ot, e in R["ocdfg_edges"].items():
    print(ot, e)
