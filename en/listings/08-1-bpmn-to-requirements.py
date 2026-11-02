# Listing from Section 8.3.2 of the textbook “Fundamentals of Business Process Analysis and Modelling in IT”.

import xml.etree.ElementTree as ET

NS = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
KIND = {"userTask": "UI / user story", "serviceTask": "function / integration",
        "businessRuleTask": "business rule (DMN)", "sendTask": "outgoing interface",
        "receiveTask": "incoming interface", "manualTask": "recording manual work"}

root = ET.parse("aerocargo-tobe.bpmn").getroot()
n = 0
for tag, kind in KIND.items():
    for el in root.iter(f"{{{NS['bpmn']}}}{tag}"):
        n += 1
        print(f"REQ-{n:03d}\t{kind}\t{el.get('name')}\t(source: {el.get('id')})")
