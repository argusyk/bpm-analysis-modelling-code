# -*- coding: utf-8 -*-
"""Перевірка коректності (soundness) BPMN-моделей: BPMN -> мережа Петрі -> Woflan.
Конвертер PM4Py не підтримує проміжні події очікування, тому перед перевіркою
вони замінюються прямим з'єднанням попередника з наступником (логіку потоку
керування це не змінює). Друга частина обчислює метрики розміру і складності моделі
(розділ 4.11.2): кількість вузлів і дуг, коефіцієнт зв'язності CNC, щільність,
складність потоку керування CFC за Кардозу і невідповідність шлюзів.
Запуск: python check_models.py"""
import warnings; warnings.filterwarnings("ignore")
import pm4py
from pm4py.objects.bpmn.obj import BPMN

def prepare(g):
    for n in list(g.get_nodes()):
        if type(n).__name__ in ("Participant", "Collaboration"):
            g.remove_node(n)
    for n in list(g.get_nodes()):
        if "IntermediateCatchEvent" in type(n).__name__:
            ins = [f.get_source() for f in g.get_flows() if f.get_target() is n]
            outs = [f.get_target() for f in g.get_flows() if f.get_source() is n]
            for fl in [f for f in g.get_flows() if n in (f.get_source(), f.get_target())]:
                g.remove_flow(fl)
            g.remove_node(n)
            for a in ins:
                for b in outs:
                    g.add_flow(BPMN.SequenceFlow(a, b))
    return g

NODE_TAGS = ("task", "userTask", "serviceTask", "sendTask", "receiveTask", "manualTask", "scriptTask",
             "businessRuleTask", "callActivity", "subProcess", "startEvent", "endEvent",
             "intermediateCatchEvent", "intermediateThrowEvent", "boundaryEvent",
             "exclusiveGateway", "parallelGateway", "inclusiveGateway", "eventBasedGateway")
GW = {"exclusiveGateway": "XOR", "parallelGateway": "AND", "inclusiveGateway": "OR", "eventBasedGateway": "XOR"}


def metrics(path):
    """Метрики розміру і складності моделі за XML-файлом BPMN (усі процеси файлу)."""
    import xml.etree.ElementTree as ET
    ns = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"
    root = ET.parse(path).getroot()
    nodes, kind, flows = set(), {}, []
    for proc in root.iter(ns + "process"):
        for el in proc.iter():
            tag = el.tag.replace(ns, "")
            if tag in NODE_TAGS:
                nodes.add(el.get("id")); kind[el.get("id")] = tag
            elif tag == "sequenceFlow":
                flows.append((el.get("sourceRef"), el.get("targetRef")))
    n, a = len(nodes), len(flows)
    out_deg = {x: sum(1 for s, _ in flows if s == x) for x in nodes}
    in_deg = {x: sum(1 for _, t in flows if t == x) for x in nodes}
    cfc, split, join = 0, {"XOR": 0, "AND": 0, "OR": 0}, {"XOR": 0, "AND": 0, "OR": 0}
    for x in nodes:
        g = GW.get(kind[x])
        if not g:
            continue
        if out_deg[x] > 1:                      # розгалуження
            cfc += {"XOR": out_deg[x], "OR": 2 ** out_deg[x] - 1, "AND": 1}[g]
            split[g] += out_deg[x]
        if in_deg[x] > 1:                       # злиття
            join[g] += in_deg[x]
    return {"вузлів": n, "дуг": a, "шлюзів": sum(1 for x in nodes if x in kind and kind[x] in GW),
            "CNC": round(a / n, 2), "щільність": round(a / (n * (n - 1)), 3), "CFC": cfc,
            "невідповідність шлюзів": sum(abs(split[g] - join[g]) for g in split)}


if __name__ == "__main__":
  import os
  os.chdir(os.path.dirname(os.path.abspath(__file__)))
  for f in ["aerocargo-asis.bpmn", "aerocargo-tobe.bpmn", "error-deadlock.bpmn"]:
    g = prepare(pm4py.read_bpmn(f))
    net, im, fm = pm4py.convert_to_petri_net(g)
    ok, diag = pm4py.check_soundness(net, im, fm)
    print(f"{f}: місць {len(net.places)}, переходів {len(net.transitions)}, коректна (sound): {ok}")
  print()
  print("Метрики розміру і складності (розділ 4.11.2):")
  for f in ["aerocargo-asis.bpmn", "aerocargo-tobe.bpmn", "error-deadlock.bpmn"]:
    print(f"  {f}: " + ", ".join(f"{k} {v}" for k, v in metrics(f).items()))
