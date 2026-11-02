# Listing from Section 9.1.2 of the textbook “Fundamentals of Business Process Analysis and Modelling in IT”.

t = get(f"{API}/tenders/{tid}")["data"]
case = t.get("tenderID", tid)
ev("Tender announced", ts(t["tenderPeriod"]["startDate"]))
ev("Bid submission deadline", ts(t["tenderPeriod"]["endDate"]))
for a in sorted(t.get("awards", []), key=lambda a: a.get("date", "")):
    if a.get("status") == "unsuccessful":
        ev("Bid rejected", ts(a.get("date")))
    elif a.get("status") == "active":
        ev("Winner awarded", ts(a.get("date")))
for c in t.get("contracts", []):
    if c.get("status") == "active":
        ev("Contract signed", ts(c.get("dateSigned")))
