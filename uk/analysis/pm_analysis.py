# -*- coding: utf-8 -*-
"""Process mining журналу АероКарго засобами PM4Py: статистика, варіанти,
граф безпосереднього слідування, виявлення моделі і перевірка відповідності
моделі «як є». Запуск: python pm_analysis.py  (результати -> results.json)"""
import os, sys, json, warnings
warnings.filterwarnings("ignore")
import pandas as pd
import pm4py

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "models"))
from check_models import prepare               # підготовка BPMN до конвертації

df = pd.read_csv(os.path.join(HERE, "..", "data", "aerocargo_export_log.csv"), sep=";", encoding="utf-8-sig")
df["timestamp"] = pd.to_datetime(df["timestamp"])
log = pm4py.format_dataframe(df, case_id="case_id", activity_key="activity", timestamp_key="timestamp")
R = {}

# 1. Загальна статистика
R["cases"] = int(df["case_id"].nunique()); R["events"] = int(len(df))
variants = pm4py.get_variants(log)
counts = sorted(((v if isinstance(v, int) else len(v)) for v in variants.values()), reverse=True)
R["variants"] = len(variants); R["top_variant_share"] = round(counts[0] / R["cases"], 3)

# 2. Час обробки на терміналі: від «Вантаж доставлено» до «Передати ULD»
g = df.pivot_table(index="case_id", columns="activity", values="timestamp", aggfunc="min")
last = df[df.activity == "Передати ULD"].groupby("case_id").timestamp.max()
ct = (last - g["Вантаж доставлено"]).dt.total_seconds() / 3600
R["ct_mean_h"] = round(ct.mean(), 2); R["ct_median_h"] = round(ct.median(), 2); R["ct_p90_h"] = round(ct.quantile(0.9), 2)
R["ct_hist"] = [int(((ct >= a) & (ct < a + 1)).sum()) for a in range(0, 16)]

# 3. Переробки, ескалації, паралельна практика
per_case = df.groupby("case_id").activity.apply(list)
R["rework_share"] = round(per_case.apply(lambda a: "Запросити виправлення" in a).mean(), 3)
R["escalation_share"] = round(per_case.apply(lambda a: "Ескалювати начальнику зміни" in a).mean(), 3)
R["parallel_share"] = round(per_case.apply(lambda a: a.index("Отримати митний дозвіл") < a.index("Пройти скринінг")).mean(), 3)
par = per_case.apply(lambda a: a.index("Отримати митний дозвіл") < a.index("Пройти скринінг"))
R["ct_mean_parallel_h"] = round(ct[par[par].index].mean(), 2)
R["ct_mean_sequential_h"] = round(ct[par[~par].index].mean(), 2)

# 4. Граф безпосереднього слідування (найчастіші дуги)
dfg, starts, ends = pm4py.discover_dfg(log)
R["dfg_top"] = [[a, b, int(n)] for (a, b), n in sorted(dfg.items(), key=lambda x: -x[1])[:12]]

# 5. Виявлення моделі індуктивним алгоритмом і її якість
net, im, fm = pm4py.discover_petri_net_inductive(log, noise_threshold=0.2)
R["discovered_fitness"] = round(pm4py.fitness_token_based_replay(log, net, im, fm)["log_fitness"], 3)
R["discovered_precision"] = round(pm4py.precision_token_based_replay(log, net, im, fm), 3)

# 6. Перевірка відповідності нормативній моделі «як є» (BPMN)
bp = prepare(pm4py.read_bpmn(os.path.join(HERE, "..", "models", "aerocargo-asis.bpmn")))
n2, i2, f2 = pm4py.convert_to_petri_net(bp)
model_acts = {t.label for t in n2.transitions if t.label}
log_m = pm4py.filter_event_attribute_values(log, "concept:name", list(model_acts), level="event", retain=True)
diag = pm4py.conformance_diagnostics_token_based_replay(log_m, n2, i2, f2)
R["asis_fitness"] = round(pm4py.fitness_token_based_replay(log_m, n2, i2, f2)["log_fitness"], 3)
R["asis_fit_traces_share"] = round(sum(d["trace_is_fit"] for d in diag) / len(diag), 3)
R["activities_outside_model"] = sorted(set(df.activity) - model_acts)

with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as _f:

    json.dump(R, _f, ensure_ascii=False, indent=1)
for k, v in R.items():
    if k not in ("ct_hist", "dfg_top"): print(f"{k}: {v}")
print("найчастіші дуги DFG:")
for a, b, n in R["dfg_top"][:8]: print(f"  {a} -> {b}: {n}")
