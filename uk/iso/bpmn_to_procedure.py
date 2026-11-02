# -*- coding: utf-8 -*-
"""Генерація чернетки документованої процедури (ISO 9001, п. 7.5) з BPMN-моделі.
Процедура містить: мету, межі, ролі (з доріжок), кроки у порядку потоку з
виконавцем і типом дії, точки рішень і записи, що мають зберігатися.
Запуск: python bpmn_to_procedure.py ../models/aerocargo-tobe.bpmn  -> procedure.md"""
import os, sys, xml.etree.ElementTree as ET

NS = {"b": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
KIND = {"userTask": "виконується працівником в інформаційній системі", "manualTask": "виконується вручну",
        "serviceTask": "виконується автоматично", "businessRuleTask": "виконується автоматично за правилами",
        "sendTask": "надсилання повідомлення", "receiveTask": "отримання повідомлення"}
TASKS = tuple(KIND) + ("task",)


def main(path, out):
    root = ET.parse(path).getroot()
    proc = root.find("b:process", NS)
    name = proc.get("name")
    lane_of = {}
    lanes = []
    for lane in proc.iter(f"{{{NS['b']}}}lane"):
        lanes.append(lane.get("name"))
        for ref in lane.findall("b:flowNodeRef", NS):
            lane_of[ref.text] = lane.get("name")
    nodes = {el.get("id"): el for el in proc if el.get("id") and not el.tag.endswith(("sequenceFlow", "laneSet"))}
    flows = [(f.get("sourceRef"), f.get("targetRef"), f.get("name") or "") for f in proc.findall("b:sequenceFlow", NS)]
    nxt = {}
    for s, t, n in flows:
        nxt.setdefault(s, []).append((t, n))
    start = next(i for i, e in nodes.items() if e.tag.endswith("startEvent"))
    # обхід у ширину – порядок кроків процедури. Він навмисно простий: його недолік (подія циклу
    # виправлень опиняється не на своєму місці) розібрано в підрозділі 10.2.2. Вправа: замініть
    # його обходом у глибину, який виводить гілку циклу одразу після рішення.
    order, seen, queue = [], set(), [start]
    while queue:
        cur = queue.pop(0)
        if cur in seen: continue
        seen.add(cur); order.append(cur)
        queue += [t for t, _ in nxt.get(cur, [])]
    L = [f"# Процедура «{name}»", "", "Чернетку згенеровано автоматично з BPMN-моделі; перед затвердженням її перевіряє власник процесу.", "",
         "## 1. Мета і межі", "", f"Процедура встановлює порядок виконання процесу «{name}». "
         f"Процес починається подією «{nodes[start].get('name')}» і завершується подіями: "
         + ", ".join(f"«{e.get('name')}»" for e in nodes.values() if e.tag.endswith("endEvent")) + ".", "",
         "## 2. Учасники (ролі)", ""] + [f"- {l}" for l in lanes] + ["", "## 3. Порядок виконання", ""]
    k = 0
    for nid in order:
        el = nodes[nid]; tag = el.tag.split("}")[1]
        if tag in TASKS:
            k += 1
            L.append(f"{k}. {el.get('name')}. Виконавець: {lane_of.get(nid, '–')}; {KIND.get(tag, 'дія')}.")
        elif tag == "exclusiveGateway" and el.get("name"):
            opts = "; ".join(f"«{n}» – перейти до «{nodes[t].get('name') or 'наступного кроку'}»" for t, n in nxt.get(nid, []))
            L.append(f"   Рішення: {el.get('name')} {opts}.")
        elif tag == "parallelGateway" and len(nxt.get(nid, [])) > 1:
            L.append("   Наступні кроки виконуються паралельно: " + ", ".join(f"«{nodes[t].get('name')}»" for t, _ in nxt[nid]) + ".")
        elif tag == "intermediateCatchEvent":
            L.append(f"   Очікування події: «{el.get('name')}».")
    L += ["", "## 4. Записи (документована інформація, що зберігається)", "",
          "- журнал подій екземплярів процесу з мітками часу і виконавцями;",
          "- результати перевірок і рішень на кожному шлюзі;",
          "- повідомлення, надіслані зовнішнім учасникам.", "",
          "## 5. Показники процесу", "", "Показники і цільові значення визначає паспорт процесу (додаток Е, таблиця Е.1).", ""]
    open(out, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "models", "aerocargo-tobe.bpmn")
    main(src, os.path.join(here, "procedure.md"))
