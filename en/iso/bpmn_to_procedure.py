# -*- coding: utf-8 -*-
"""Generates a draft documented procedure (ISO 9001, clause 7.5) from a BPMN model.
The procedure contains: purpose, scope, roles (from the lanes), steps in flow order with
the performer and the type of activity, decision points and the records to be retained.
Run: python bpmn_to_procedure.py ../models/aerocargo-tobe.bpmn  -> procedure.md"""
import os, sys, xml.etree.ElementTree as ET

NS = {"b": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
KIND = {"userTask": "performed by an employee in the information system", "manualTask": "performed manually",
        "serviceTask": "performed automatically", "businessRuleTask": "performed automatically by rules",
        "sendTask": "sending a message", "receiveTask": "receiving a message"}
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
    # breadth-first traversal – the order of the procedure steps. It is deliberately simple: its flaw (the
    # correction-loop event ends up in the wrong place) is discussed in Section 10.2.2. Exercise: replace it
    # with a depth-first traversal that outputs the loop branch right after the decision.
    order, seen, queue = [], set(), [start]
    while queue:
        cur = queue.pop(0)
        if cur in seen: continue
        seen.add(cur); order.append(cur)
        queue += [t for t, _ in nxt.get(cur, [])]
    L = [f"# Procedure \"{name}\"", "", "The draft was generated automatically from the BPMN model; it is reviewed by the process owner before approval.", "",
         "## 1. Purpose and scope", "", f"The procedure establishes how the process \"{name}\" is performed. "
         f"The process starts with the event \"{nodes[start].get('name')}\" and ends with the events: "
         + ", ".join(f"\"{e.get('name')}\"" for e in nodes.values() if e.tag.endswith("endEvent")) + ".", "",
         "## 2. Participants (roles)", ""] + [f"- {l}" for l in lanes] + ["", "## 3. Procedure", ""]
    k = 0
    for nid in order:
        el = nodes[nid]; tag = el.tag.split("}")[1]
        if tag in TASKS:
            k += 1
            L.append(f"{k}. {el.get('name')}. Performer: {lane_of.get(nid, '–')}; {KIND.get(tag, 'activity')}.")
        elif tag == "exclusiveGateway" and el.get("name"):
            opts = "; ".join(f"\"{n}\" – go to \"{nodes[t].get('name') or 'the next step'}\"" for t, n in nxt.get(nid, []))
            L.append(f"   Decision: {el.get('name')} {opts}.")
        elif tag == "parallelGateway" and len(nxt.get(nid, [])) > 1:
            L.append("   The following steps are performed in parallel: " + ", ".join(f"\"{nodes[t].get('name')}\"" for t, _ in nxt[nid]) + ".")
        elif tag == "intermediateCatchEvent":
            L.append(f"   Waiting for the event: \"{el.get('name')}\".")
    L += ["", "## 4. Records (retained documented information)", "",
          "- the event log of process instances with timestamps and performers;",
          "- the results of checks and decisions at each gateway;",
          "- messages sent to external participants.", "",
          "## 5. Process indicators", "", "The indicators and target values are defined in the process passport (Appendix F, Table F.1).", ""]
    open(out, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "models", "aerocargo-tobe.bpmn")
    main(src, os.path.join(here, "procedure.md"))
