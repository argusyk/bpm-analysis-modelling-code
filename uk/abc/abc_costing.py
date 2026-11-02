# -*- coding: utf-8 -*-
"""Облік витрат за видами діяльності (ABC) процесу обробки експортних відправок АероКарго.
Ресурси -> дії (за драйверами ресурсів) -> об'єкти витрат (за драйверами дій).
Порівнюється з традиційним розподілом накладних витрат пропорційно до ваги.
Запуск: python abc_costing.py  (результати -> results.json)"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))

# 1. Витрати ресурсів за місяць, ум. од.
# (узгоджено з таблицею 3.4: ~38 ум. од. на тонну експортного вантажу)
resources = {"Персонал складу": 5700, "Служба документації": 2450, "Лінія скринінгу": 2050,
             "Навантажувачі і рампа": 1640, "ІТ-системи": 1224}
# 2. Драйвери ресурсів: частки ресурсу, що споживає кожна дія
consumption = {
    "Персонал складу":       {"Приймання вантажу": 0.55, "Формування ULD": 0.35, "Обробка спецвантажів": 0.10},
    "Служба документації":   {"Перевірка документів": 0.60, "Виправлення документів": 0.25, "Митне оформлення": 0.15},
    "Лінія скринінгу":       {"Скринінг": 1.00},
    "Навантажувачі і рампа": {"Приймання вантажу": 0.40, "Формування ULD": 0.60},
    "ІТ-системи":            {"Перевірка документів": 0.40, "Митне оформлення": 0.30, "Приймання вантажу": 0.30}}
# 3. Об'єкти витрат: споживання драйверів дій на одну відправку і обсяг за місяць
objects = {  # на одну відправку
    "Стандартна відправка (5 місць, 150 кг)": {"Приймання вантажу": 5, "Формування ULD": 0.17, "Перевірка документів": 1.2,
                                               "Виправлення документів": 0.25, "Митне оформлення": 1, "Скринінг": 0.2},
    "Небезпечний вантаж (2 місця, 60 кг)": {"Приймання вантажу": 2, "Формування ULD": 0.5, "Обробка спецвантажів": 1,
                                            "Перевірка документів": 3, "Виправлення документів": 0.8, "Митне оформлення": 1,
                                            "Скринінг": 0.6}}
volume = {"Стандартна відправка (5 місць, 150 кг)": 2220, "Небезпечний вантаж (2 місця, 60 кг)": 180}
weights = {"Стандартна відправка (5 місць, 150 кг)": 150, "Небезпечний вантаж (2 місця, 60 кг)": 60}
UNITS = {"Приймання вантажу": "вантажних місць", "Формування ULD": "ULD", "Обробка спецвантажів": "спецвідправок",
         "Перевірка документів": "перевірок", "Виправлення документів": "виправлень",
         "Митне оформлення": "декларацій", "Скринінг": "годин скринінгу"}
# обсяги драйверів дій виводяться з асортименту, тож розподіл завжди узгоджений
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
print("витрати дій:", R["activity_cost"])
print("ставки драйверів:", R["driver_rate"])
print("обсяги драйверів:", {a: round(v[1],1) for a, v in drivers.items()}); print("звірка: сума за об'єктами =", check, "із", total); print("витрати на тонну:", per_tonne); print("ABC:", abc); print("традиційно (за вагою):", traditional)
