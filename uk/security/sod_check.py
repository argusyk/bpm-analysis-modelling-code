# -*- coding: utf-8 -*-
"""Перевірка розподілу обов'язків (Segregation of Duties, SoD) за журналом подій.
Правила задають пари дій, які в межах одного кейсу не може виконувати одна особа.
Для демонстрації генерується журнал процесу закупівлі з кількома порушеннями.
Запуск: python sod_check.py  (результати -> results.json)"""
import csv, json, os, random
from collections import Counter, defaultdict
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = [("Створити заявку на закупівлю", "Погодити заявку на закупівлю"),
         ("Погодити заявку на закупівлю", "Підтвердити отримання товару"),
         ("Підтвердити отримання товару", "Затвердити оплату рахунку"),
         ("Створити заявку на закупівлю", "Затвердити оплату рахунку")]
STEPS = ["Створити заявку на закупівлю", "Погодити заявку на закупівлю", "Підтвердити отримання товару",
         "Затвердити оплату рахунку"]
POOL_REDESIGNED = {"Створити заявку на закупівлю": ["ініціатор_01", "ініціатор_02", "ініціатор_03"],
        "Погодити заявку на закупівлю": ["керівник_01", "керівник_02"],
        "Підтвердити отримання товару": ["комірник_01", "комірник_02"],
        "Затвердити оплату рахунку": ["фінансист_01", "фінансист_02"]}
POOL = {"Створити заявку на закупівлю": ["ініціатор_01", "ініціатор_02", "ініціатор_03", "керівник_01"],
        "Погодити заявку на закупівлю": ["керівник_01", "керівник_02"],
        "Підтвердити отримання товару": ["комірник_01", "комірник_02", "керівник_02"],
        "Затвердити оплату рахунку": ["фінансист_01", "фінансист_02"]}


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
        if random.random() < 0.03:                       # «сам собі погодив»
            who["Погодити заявку на закупівлю"] = who["Створити заявку на закупівлю"] = "керівник_01"
        if random.random() < 0.02:                       # погодив і сам прийняв товар
            who["Підтвердити отримання товару"] = who["Погодити заявку на закупівлю"] = "керівник_02"
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
    for name, pool in (("поточні ролі", POOL), ("перепроєктовані ролі", POOL_REDESIGNED)):
        log = os.path.join(HERE, "procurement_log.csv" if pool is POOL else "procurement_log_redesigned.csv")
        generate(log, pool=pool)
        cases, v = check(log)
        R[name] = {"cases": len(cases), "violations": len(v), "cases_with_violation": len({x[0] for x in v}),
                   "violation_rate": round(len({x[0] for x in v}) / len(cases), 3),
                   "by_rule": Counter(f"{a} / {b}" for _, a, b, _ in v), "by_person": Counter(p for *_, p in v)}
        r = R[name]
        print(f"[{name}] кейсів: {r['cases']}, порушень: {r['violations']}, кейсів з порушеннями: {r['cases_with_violation']} ({r['violation_rate']:.1%})")
        for k, n in r["by_rule"].items(): print(f"    правило «{k}»: {n}")
        for k, n in r["by_person"].items(): print(f"    виконавець {k}: {n}")
    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as _f:
        json.dump(R, _f, ensure_ascii=False, indent=1)