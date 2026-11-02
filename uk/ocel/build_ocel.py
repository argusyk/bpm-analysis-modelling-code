# -*- coding: utf-8 -*-
"""Об'єктно-центричний журнал подій (OCEL 2.0) процесу закупівлі (розділ 9.1.5).
Об'єкти чотирьох типів: заявка, замовлення, поставка, рахунок. Одна подія може
стосуватися кількох об'єктів: «Звірити рахунок» пов'язує рахунок, одне або два
замовлення і всі їхні поставки. Програма будує журнал, зберігає його у форматі
OCEL 2.0 (JSON), виявляє об'єктно-центричний граф (OC-DFG) і показує, які спотворення
дає «сплощення» журналу до класичного вигляду з одним ідентифікатором кейсу.
Запуск: python build_ocel.py  (-> procurement.jsonocel, results.json)"""
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


pending = []                     # замовлення, що чекають на рахунок: (po, [поставки], час)
for i in range(300):
    t = t0 + timedelta(hours=i * 2.5)
    rq = obj(f"ЗК-{i + 1:04d}", "заявка")
    event("Створити заявку", t, [rq])
    t += timedelta(hours=random.uniform(2, 20))
    event("Погодити заявку", t, [rq])
    if random.random() < 0.05:                       # відхилені заявки
        continue
    t += timedelta(hours=random.uniform(1, 8))
    po = obj(f"ЗМ-{i + 1:04d}", "замовлення")
    event("Створити замовлення", t, [rq, po])
    dels = []
    for k in range(2 if random.random() < 0.3 else 1):   # 30 % замовлень – частковими поставками
        t += timedelta(hours=random.uniform(24, 96))
        d = obj(f"ПС-{i + 1:04d}-{k + 1}", "поставка")
        event("Отримати поставку", t, [po, d]); dels.append(d)
    pending.append((po, dels, t))
    # 20 % рахунків постачальник виставляє одним документом на два замовлення
    if len(pending) == 2 or (len(pending) == 1 and random.random() > 0.2):
        tt = max(x[2] for x in pending) + timedelta(hours=random.uniform(4, 48))
        inv = obj(f"РХ-{i + 1:04d}", "рахунок")
        pos = [x[0] for x in pending]; ds = [d for x in pending for d in x[1]]
        event("Отримати рахунок", tt, [inv] + pos)
        tt += timedelta(hours=random.uniform(2, 30))
        event("Звірити рахунок", tt, [inv] + pos + ds)
        tt += timedelta(hours=random.uniform(24, 120))
        event("Оплатити рахунок", tt, [inv])
        pending = []

ocel = OCEL(events=pd.DataFrame(ev), objects=pd.DataFrame(objs), relations=pd.DataFrame(rel))
pm4py.write_ocel2_json(ocel, os.path.join(HERE, "procurement.jsonocel"))

R = {"events": len(ev), "objects": pd.DataFrame(objs)["ocel:type"].value_counts().to_dict(), "relations": len(rel)}
# сплощення: скільки подій отримує кожен класичний журнал і скільки з них – копії
R["flattening"] = {}
for ot in ["заявка", "замовлення", "поставка", "рахунок"]:
    flat = pm4py.ocel_flattening(ocel, ot)
    n = len(flat); uniq = flat["ocel:eid"].nunique() if "ocel:eid" in flat.columns else None
    acts = sorted(flat["concept:name"].unique())
    R["flattening"][ot] = {"rows": n, "unique_events": uniq, "activities": len(acts)}
# кількість подій «Звірити рахунок», що стосуються кількох замовлень
multi = pd.DataFrame(rel).query("`ocel:activity` == 'Звірити рахунок' and `ocel:type` == 'замовлення'").groupby("ocel:eid").size()
R["match_events"] = int(len(multi)); R["match_events_two_orders"] = int((multi > 1).sum())
ocdfg = pm4py.discover_ocdfg(ocel)
R["ocdfg_edges"] = {ot: {f"{a} -> {b}": len(v) for (a, b), v in e.items()}
                    for ot, e in ocdfg["edges"]["event_couples"].items()}
with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as _f:
    json.dump(R, _f, ensure_ascii=False, indent=1)
print("подій:", R["events"], "об'єктів:", R["objects"], "зв'язків подія-об'єкт:", R["relations"])
print("подій звіряння:", R["match_events"], "з них на два замовлення:", R["match_events_two_orders"])
for ot, v in R["flattening"].items():
    print(f"сплощення за типом «{ot}»: рядків {v['rows']}, унікальних подій {v['unique_events']}, дій {v['activities']}")
for ot, e in R["ocdfg_edges"].items():
    print(ot, e)
