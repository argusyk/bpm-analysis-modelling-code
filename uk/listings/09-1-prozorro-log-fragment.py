# Лістинг з підрозділу 9.1.2 посібника «Основи аналізу та моделювання бізнес-процесів в ІТ».

t = get(f"{API}/tenders/{tid}")["data"]
case = t.get("tenderID", tid)
ev("Оголошення закупівлі", ts(t["tenderPeriod"]["startDate"]))
ev("Кінцевий строк подання пропозицій", ts(t["tenderPeriod"]["endDate"]))
for a in sorted(t.get("awards", []), key=lambda a: a.get("date", "")):
    if a.get("status") == "unsuccessful":
        ev("Відхилення пропозиції учасника", ts(a.get("date")))
    elif a.get("status") == "active":
        ev("Визначення переможця", ts(a.get("date")))
for c in t.get("contracts", []):
    if c.get("status") == "active":
        ev("Підписання договору", ts(c.get("dateSigned")))
