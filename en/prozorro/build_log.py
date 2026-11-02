# -*- coding: utf-8 -*-
"""Building an event log from open Prozorro data (public API, version 2.5).
Selects open tenders (procurementMethodType = aboveThreshold) in final
statuses, downloads the full descriptions and turns the key dates into process events.
Run: python build_log.py [number_of_procurements] [feed_offset]
Result: prozorro_log.csv (event log) and prozorro_tenders.csv (procurement attributes).
Data source: https://public-api.prozorro.gov.ua (open public procurement data)."""
import csv, json, os, sys, time, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://public-api.prozorro.gov.ua/api/2.5"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
OFFSET = sys.argv[2] if len(sys.argv) > 2 else "1780300000"   # position in the change feed (≈ June 2026)
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


# 1. Selecting procurements from the change feed
ids, url = [], f"{API}/tenders?offset={OFFSET}&limit=100&opt_fields=status,procurementMethodType"
while len(ids) < N:
    page = get(url)
    ids += [x["id"] for x in page["data"]
            if x.get("procurementMethodType") == "aboveThreshold" and x.get("status") in FINAL]
    url = page["next_page"]["uri"]
ids = ids[:N]

# 2. Turning procurement descriptions into events
events, tenders = [], []
for i, tid in enumerate(ids):
    t = get(f"{API}/tenders/{tid}")["data"]
    case = t.get("tenderID", tid)
    ev = lambda act, when: events.append((case, act, when)) if when else None
    ev("Tender announced", ts((t.get("tenderPeriod") or {}).get("startDate")))
    ev("Enquiry period ended", ts((t.get("enquiryPeriod") or {}).get("endDate")))
    ev("Bid submission deadline", ts((t.get("tenderPeriod") or {}).get("endDate")))
    auction = (t.get("auctionPeriod") or {}).get("endDate")
    if not auction and t.get("lots"):
        auction = (t["lots"][0].get("auctionPeriod") or {}).get("endDate")
    ev("Auction held", ts(auction))
    for c in t.get("complaints", []):
        ev("Complaint submitted", ts(c.get("dateSubmitted")))
    for a in sorted(t.get("awards", []), key=lambda a: a.get("date", "")):
        for c in a.get("complaints", []):
            ev("Complaint submitted", ts(c.get("dateSubmitted")))
        if a.get("status") == "unsuccessful":
            ev("Bid rejected", ts(a.get("date")))
        elif a.get("status") == "active":
            ev("Winner awarded", ts(a.get("date")))
    for c in t.get("contracts", []):
        if c.get("status") == "active":
            ev("Contract signed", ts(c.get("dateSigned") or c.get("date")))
    if t["status"] == "unsuccessful":
        ev("Tender unsuccessful", ts(t.get("date")))
    if t["status"] == "cancelled":
        ev("Tender cancelled", ts(t.get("date")))
    tenders.append((case, t["status"], (t.get("value") or {}).get("amount"), len(t.get("bids", [])),
                    (t.get("procuringEntity") or {}).get("kind"), (t.get("mainProcurementCategory") or "")))
    if (i + 1) % 50 == 0:
        print(f"processed {i + 1} procurements")

events.sort(key=lambda e: (e[0], e[2]))
with open(os.path.join(HERE, "prozorro_log.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["case_id", "activity", "timestamp"])
    w.writerows((c, a, d.strftime("%Y-%m-%d %H:%M:%S")) for c, a, d in events)
with open(os.path.join(HERE, "prozorro_tenders.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["case_id", "status", "value_uah", "bids", "entity_kind", "category"])
    w.writerows(tenders)
print(f"procurements: {len(tenders)}, events: {len(events)}")
