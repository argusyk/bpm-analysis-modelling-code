# Лістинг з підрозділу 8.3.2 посібника «Основи аналізу та моделювання бізнес-процесів в ІТ».

import xml.etree.ElementTree as ET

NS = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
KIND = {"userTask": "UI / користувацька історія", "serviceTask": "функція / інтеграція",
        "businessRuleTask": "бізнес-правило (DMN)", "sendTask": "вихідний інтерфейс",
        "receiveTask": "вхідний інтерфейс", "manualTask": "фіксація ручної роботи"}

root = ET.parse("aerocargo-tobe.bpmn").getroot()
n = 0
for tag, kind in KIND.items():
    for el in root.iter(f"{{{NS['bpmn']}}}{tag}"):
        n += 1
        print(f"REQ-{n:03d}\t{kind}\t{el.get('name')}\t(джерело: {el.get('id')})")
