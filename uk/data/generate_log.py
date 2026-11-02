# -*- coding: utf-8 -*-
"""Генератор синтетичного журналу подій процесу «як є» АероКарго.
Параметри узгоджено з таблицею 6.1 посібника (середні очікування й тривалості,
частка переробок документів 29 %, пікове очікування на скринінг, 7 % відправок
з митним запитом до завершення скринінгу). Метрика parallel_share у pm_analysis.py
рахує лише відправки, у яких дозвіл отримано раніше за скринінг (~3 %), див. підрозділ 6.8.3.
Запуск: python generate_log.py [кількість_відправок]  ->  aerocargo_export_log.csv"""
import csv, os, random, sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
random.seed(2026)
T0 = datetime(2026, 3, 2, 0, 0)

def awb():
    serial = random.randint(1_000_000, 9_999_999)
    return f"176-{serial}{serial % 7}"          # контрольна цифра за правилом IATA

def work(mean):                                  # тривалість роботи: гамма з k = 4
    return random.gammavariate(4, mean / 4)

def wait(mean):                                  # очікування: експоненційний розподіл
    return random.expovariate(1 / mean)

def arrival_hour():                              # піковий профіль доставки вантажів
    return random.choices(range(24), weights=[1,1,1,1,1,2,4,6,9,12,12,9,7,6,5,5,4,3,3,2,2,1,1,1])[0]

rows = []
for i in range(N):
    case = awb()
    day = i * 24 / 80                             # ~80 відправок на добу
    t = T0 + timedelta(hours=int(day // 24) * 24 + arrival_hour() + random.random())
    ev = lambda act, when, res: rows.append((case, act, when.strftime("%Y-%m-%d %H:%M:%S"), res))
    ev("Підтвердити бронювання", t - timedelta(hours=random.uniform(12, 60)), "комерційний відділ")
    ev("Вантаж доставлено", t, "склад")
    t += timedelta(hours=wait(0.50) + work(0.35)); ev("Прийняти вантаж", t, f"комірник {random.randint(1, 9):02d}")
    t += timedelta(hours=wait(1.28) + work(0.15)); ev("Перевірити дані e-AWB", t, f"агент {random.randint(1, 4):02d}")
    while random.random() < 0.29:                # цикл виправлення документів
        t += timedelta(hours=0.03); ev("Запросити виправлення", t, "служба документації")
        if random.random() < 0.07:
            t += timedelta(hours=4); ev("Ескалювати начальнику зміни", t, "начальник зміни")
        t += timedelta(hours=wait(1.0)); ev("Отримати виправлення", t, "експедитор")
        t += timedelta(hours=work(0.15)); ev("Перевірити дані e-AWB", t, f"агент {random.randint(1, 4):02d}")
    parallel = random.random() < 0.07            # неформальна практика: митниця паралельно
    peak = 10 <= t.hour < 12
    t_screen = t + timedelta(hours=wait(3.0 if peak else 0.9) + work(0.25))
    if random.random() < 0.035:
        ev("Пройти скринінг", t_screen, "САБ")
        t_screen += timedelta(hours=work(1.0)); ev("Переупакувати", t_screen, f"комірник {random.randint(1, 9):02d}")
        t_screen += timedelta(hours=wait(0.5) + work(0.25))
    if parallel:
        t_cust = t + timedelta(hours=wait(1.0) + work(0.2))
        ev("Отримати митний дозвіл", t_cust, "митний пост")
        ev("Пройти скринінг", t_screen, "САБ")
        t = max(t_cust, t_screen)
    else:
        ev("Пройти скринінг", t_screen, "САБ")
        t = t_screen + timedelta(hours=wait(1.0) + work(0.2)); ev("Отримати митний дозвіл", t, "митний пост")
    t += timedelta(hours=wait(0.5) + work(0.3)); ev("Передати ULD", t, "група ULD")

rows.sort(key=lambda r: (r[2], r[0]))
out = os.path.join(HERE, "aerocargo_export_log.csv")
with open(out, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["case_id", "activity", "timestamp", "resource"])
    w.writerows(rows)
print(f"збережено {out}: {N} відправок, {len(rows)} подій")
