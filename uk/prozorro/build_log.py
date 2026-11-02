# -*- coding: utf-8 -*-
"""Побудова журналу подій з відкритих даних Prozorro (публічний API, версія 2.5).
Відбирає відкриті торги (procurementMethodType = aboveThreshold) у кінцевих
статусах, завантажує повні описи і перетворює ключові дати на події процесу.
Запуск: python build_log.py [кількість_закупівель] [offset_стрічки]
Результат: prozorro_log.csv (журнал подій) і prozorro_tenders.csv (атрибути закупівель).
Джерело даних: https://public-api.prozorro.gov.ua (відкриті дані публічних закупівель)."""
import csv, json, os, sys, time, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://public-api.prozorro.gov.ua/api/2.5"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
OFFSET = sys.argv[2] if len(sys.argv) > 2 else "1780300000"   # позиція стрічки змін (≈ червень 2026)
FINAL = ("complete", "unsuccessful", "cancelled")


def get(url, tries=3):
    for k in range(tries):
        try:
            return json.loads(urllib.request.urlopen(url, timeout=30).read())
        except Exception:
            time.sleep(2 * (k + 1))
    raise RuntimeError(url)


def ts(s):
    if not s:
        return None
    return datetime.fromisoformat(s).astimezone(timezone.utc).replace(tzinfo=None)


# 1. Відбір закупівель зі стрічки змін
ids, url = [], f"{API}/tenders?offset={OFFSET}&limit=100&opt_fields=status,procurementMethodType"
while len(ids) < N:
    page = get(url)
    ids += [x["id"] for x in page["data"]
            if x.get("procurementMethodType") == "aboveThreshold" and x.get("status") in FINAL]
    url = page["next_page"]["uri"]
ids = ids[:N]

# 2. Перетворення описів закупівель на події
events, tenders = [], []
for i, tid in enumerate(ids):
    t = get(f"{API}/tenders/{tid}")["data"]
    case = t.get("tenderID", tid)
    ev = lambda act, when: events.append((case, act, when)) if when else None
    ev("Оголошення закупівлі", ts((t.get("tenderPeriod") or {}).get("startDate")))
    ev("Завершення періоду уточнень", ts((t.get("enquiryPeriod") or {}).get("endDate")))
    ev("Кінцевий строк подання пропозицій", ts((t.get("tenderPeriod") or {}).get("endDate")))
    auction = (t.get("auctionPeriod") or {}).get("endDate")
    if not auction and t.get("lots"):
        auction = (t["lots"][0].get("auctionPeriod") or {}).get("endDate")
    ev("Проведення аукціону", ts(auction))
    for c in t.get("complaints", []):
        ev("Подання скарги", ts(c.get("dateSubmitted")))
    for a in sorted(t.get("awards", []), key=lambda a: a.get("date", "")):
        for c in a.get("complaints", []):
            ev("Подання скарги", ts(c.get("dateSubmitted")))
        if a.get("status") == "unsuccessful":
            ev("Відхилення пропозиції учасника", ts(a.get("date")))
        elif a.get("status") == "active":
            ev("Визначення переможця", ts(a.get("date")))
    for c in t.get("contracts", []):
        if c.get("status") == "active":
            ev("Підписання договору", ts(c.get("dateSigned") or c.get("date")))
    if t["status"] == "unsuccessful":
        ev("Закупівля не відбулася", ts(t.get("date")))
    if t["status"] == "cancelled":
        ev("Скасування закупівлі", ts(t.get("date")))
    tenders.append((case, t["status"], (t.get("value") or {}).get("amount"), len(t.get("bids", [])),
                    (t.get("procuringEntity") or {}).get("kind"), (t.get("mainProcurementCategory") or "")))
    if (i + 1) % 50 == 0:
        print(f"оброблено {i + 1} закупівель")

events.sort(key=lambda e: (e[0], e[2]))
with open(os.path.join(HERE, "prozorro_log.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["case_id", "activity", "timestamp"])
    w.writerows((c, a, d.strftime("%Y-%m-%d %H:%M:%S")) for c, a, d in events)
with open(os.path.join(HERE, "prozorro_tenders.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["case_id", "status", "value_uah", "bids", "entity_kind", "category"])
    w.writerows(tenders)
print(f"закупівель: {len(tenders)}, подій: {len(events)}")
