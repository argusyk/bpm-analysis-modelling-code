# -*- coding: utf-8 -*-
"""Generates the AeroCargo process models in BPMN 2.0 XML format with diagram
information (BPMN DI), so the files open in Camunda Modeler and bpmn.io.
Run: python make_bpmn.py  ->  aerocargo-asis.bpmn, aerocargo-tobe.bpmn"""
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = {"startEvent": (36, 36), "endEvent": (36, 36), "intermediateCatchEvent": (36, 36),
        "exclusiveGateway": (50, 50), "parallelGateway": (50, 50), "eventBasedGateway": (50, 50)}
TASK = (110, 70)


def build(pid, name, lanes, nodes, flows, fname):
    """lanes: [(id, name)] top to bottom; nodes: [(id, type, name, x_center, lane_id, extra_xml)];
    flows: [(id, src, dst, name, condition_or_None)]"""
    LH, LX, LW = 150, 190, 1520          # lane height, pool offset, width
    lane_y = {lid: 80 + i * LH for i, (lid, _) in enumerate(lanes)}
    pos = {}
    for nid, typ, nm, xc, lane, _ in nodes:
        w, h = SIZE.get(typ, TASK)
        yc = lane_y[lane] + LH / 2
        pos[nid] = (xc - w / 2, yc - h / 2, w, h)
    X = []
    X.append('<?xml version="1.0" encoding="UTF-8"?>')
    X.append('<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" '
             'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
             'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
             'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
             'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
             f'id="defs_{pid}" targetNamespace="http://aerocargo.example/bpmn">')
    X.append(f'  <collaboration id="collab_{pid}"><participant id="part_{pid}" name="AeroCargo Service" processRef="{pid}"/></collaboration>')
    X.append(f'  <process id="{pid}" name="{escape(name)}" isExecutable="false">')
    X.append('    <laneSet id="ls1">')
    for lid, lname in lanes:
        refs = "".join(f"<flowNodeRef>{n[0]}</flowNodeRef>" for n in nodes if n[4] == lid)
        X.append(f'      <lane id="{lid}" name="{escape(lname)}">{refs}</lane>')
    X.append('    </laneSet>')
    inc = {n[0]: [] for n in nodes}; out = {n[0]: [] for n in nodes}
    for fid, s, d, _, _ in flows:
        out[s].append(fid); inc[d].append(fid)
    for nid, typ, nm, _, _, extra in nodes:
        body = "".join(f"<incoming>{f}</incoming>" for f in inc[nid]) + "".join(f"<outgoing>{f}</outgoing>" for f in out[nid])
        X.append(f'    <{typ} id="{nid}" name="{escape(nm)}">{body}{extra or ""}</{typ}>')
    for fid, s, d, nm, cond in flows:
        c = f'<conditionExpression xsi:type="tFormalExpression">{escape(cond)}</conditionExpression>' if cond else ""
        X.append(f'    <sequenceFlow id="{fid}" name="{escape(nm or "")}" sourceRef="{s}" targetRef="{d}">{c}</sequenceFlow>')
    X.append('  </process>')
    # ---- DI ----
    X.append(f'  <bpmndi:BPMNDiagram id="dia_{pid}"><bpmndi:BPMNPlane id="plane_{pid}" bpmnElement="collab_{pid}">')
    H = LH * len(lanes)
    X.append(f'    <bpmndi:BPMNShape id="part_{pid}_di" bpmnElement="part_{pid}" isHorizontal="true"><dc:Bounds x="{LX-30}" y="80" width="{LW+30}" height="{H}"/></bpmndi:BPMNShape>')
    for lid, _ in lanes:
        X.append(f'    <bpmndi:BPMNShape id="{lid}_di" bpmnElement="{lid}" isHorizontal="true"><dc:Bounds x="{LX}" y="{lane_y[lid]}" width="{LW}" height="{LH}"/></bpmndi:BPMNShape>')
    for nid, typ, *_ in nodes:
        x, y, w, h = pos[nid]
        X.append(f'    <bpmndi:BPMNShape id="{nid}_di" bpmnElement="{nid}"><dc:Bounds x="{x:.0f}" y="{y:.0f}" width="{w}" height="{h}"/></bpmndi:BPMNShape>')
    for fid, s, d, _, _ in flows:
        sx, sy, sw, sh = pos[s]; dx, dy, dw, dh = pos[d]
        a = (sx + sw, sy + sh / 2); b = (dx, dy + dh / 2)
        if dx + dw / 2 < sx + sw / 2:                  # backward flow: route over the top
            top = min(sy, dy) - 30
            pts = [(sx + sw / 2, sy), (sx + sw / 2, top), (dx + dw / 2, top), (dx + dw / 2, dy)]
        elif abs(a[1] - b[1]) < 1:
            pts = [a, b]
        else:
            mx = (a[0] + b[0]) / 2
            pts = [a, (mx, a[1]), (mx, b[1]), b]
        wp = "".join(f'<di:waypoint x="{x:.0f}" y="{y:.0f}"/>' for x, y in pts)
        X.append(f'    <bpmndi:BPMNEdge id="{fid}_di" bpmnElement="{fid}">{wp}</bpmndi:BPMNEdge>')
    X.append('  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>')
    X.append('</definitions>')
    open(os.path.join(HERE, fname), "w", encoding="utf-8").write("\n".join(X))
    print("saved:", fname)


MSG = '<messageEventDefinition/>'
TMR = '<timerEventDefinition><timeDuration xsi:type="tFormalExpression">PT4H</timeDuration></timerEventDefinition>'

# ---------- "as-is" model ----------
lanes = [("L_com", "Commercial department"), ("L_doc", "Documentation service"), ("L_wh", "Export warehouse"), ("L_uld", "ULD team")]
nodes = [
    ("S", "startEvent", "Booking received", 260, "L_com", MSG),
    ("T_confirm", "userTask", "Confirm booking", 370, "L_com", ""),
    ("E_arrived", "intermediateCatchEvent", "Cargo delivered", 500, "L_wh", MSG),
    ("T_accept", "userTask", "Accept cargo", 610, "L_wh", ""),
    ("G_merge", "exclusiveGateway", "", 700, "L_doc", ""),
    ("T_check", "userTask", "Check e-AWB data", 790, "L_doc", ""),
    ("G_valid", "exclusiveGateway", "Data correct?", 900, "L_doc", ""),
    ("T_fix", "sendTask", "Request correction", 900, "L_com", ""),
    ("E_fixed", "intermediateCatchEvent", "Correction received", 700, "L_com", MSG),
    ("T_screen", "userTask", "Pass screening", 1020, "L_wh", ""),
    ("T_customs", "userTask", "Obtain customs release", 1170, "L_doc", ""),
    ("T_uld", "manualTask", "Hand over ULD", 1330, "L_uld", ""),
    ("E_end", "endEvent", "Shipment handed over to carrier", 1470, "L_uld", ""),
]
flows = [
    ("f1", "S", "T_confirm", "", None), ("f2", "T_confirm", "E_arrived", "", None),
    ("f3", "E_arrived", "T_accept", "", None), ("f4", "T_accept", "G_merge", "", None),
    ("f4b", "G_merge", "T_check", "", None), ("f5", "T_check", "G_valid", "", None),
    ("f6", "G_valid", "T_fix", "no", "${not awbValid}"), ("f7", "T_fix", "E_fixed", "", None),
    ("f8", "E_fixed", "G_merge", "", None),
    ("f9", "G_valid", "T_screen", "yes", "${awbValid}"), ("f10", "T_screen", "T_customs", "", None),
    ("f11", "T_customs", "T_uld", "", None), ("f12", "T_uld", "E_end", "", None),
]
build("aerocargo_asis", "Acceptance and handling of an export shipment (as-is)", lanes, nodes, flows, "aerocargo-asis.bpmn")

# ---------- "to-be" model ----------
nodes = [
    ("S", "startEvent", "Booking with e-AWB received", 250, "L_com", MSG),
    ("G_merge", "exclusiveGateway", "", 330, "L_com", ""),
    ("T_validate", "businessRuleTask", "Validate e-AWB", 400, "L_com", ""),
    ("G_valid", "exclusiveGateway", "Data correct?", 500, "L_com", ""),
    ("T_fix", "sendTask", "Request correction", 500, "L_doc", ""),
    ("E_fixed", "intermediateCatchEvent", "Correction received", 330, "L_doc", MSG),
    ("T_slot", "sendTask", "Confirm delivery slot", 600, "L_com", ""),
    ("E_arrived", "intermediateCatchEvent", "Cargo delivered", 720, "L_wh", MSG),
    ("T_accept", "userTask", "Accept cargo", 830, "L_wh", ""),
    ("P_split", "parallelGateway", "", 960, "L_wh", ""),
    ("T_screen", "userTask", "Pass screening", 1080, "L_wh", ""),
    ("T_customs", "userTask", "Obtain customs release", 1080, "L_doc", ""),
    ("P_join", "parallelGateway", "", 1200, "L_wh", ""),
    ("T_uld", "manualTask", "Hand over ULD", 1330, "L_uld", ""),
    ("E_end", "endEvent", "Shipment handed over to carrier", 1470, "L_uld", ""),
]
flows = [
    ("f1", "S", "G_merge", "", None), ("f1b", "G_merge", "T_validate", "", None), ("f2", "T_validate", "G_valid", "", None),
    ("f3", "G_valid", "T_fix", "no", "${not awbValid}"), ("f4", "T_fix", "E_fixed", "", None),
    ("f5", "E_fixed", "G_merge", "", None),
    ("f6", "G_valid", "T_slot", "yes", "${awbValid}"), ("f7", "T_slot", "E_arrived", "", None),
    ("f8", "E_arrived", "T_accept", "", None), ("f9", "T_accept", "P_split", "", None),
    ("f10", "P_split", "T_screen", "", None), ("f11", "P_split", "T_customs", "", None),
    ("f12", "T_screen", "P_join", "", None), ("f13", "T_customs", "P_join", "", None),
    ("f14", "P_join", "T_uld", "", None), ("f15", "T_uld", "E_end", "", None),
]
build("aerocargo_tobe", "Acceptance and handling of an export shipment (to-be)", lanes, nodes, flows, "aerocargo-tobe.bpmn")

# ---------- deliberately erroneous model for the practicum (deadlock) ----------
lanes = [("L1", "Performer 1"), ("L2", "Performer 2")]
nodes = [("S", "startEvent", "Start", 260, "L1", ""), ("G1", "exclusiveGateway", "Condition?", 370, "L1", ""),
         ("A", "userTask", "Activity A", 480, "L1", ""), ("B", "userTask", "Activity B", 480, "L2", ""),
         ("G2", "parallelGateway", "", 600, "L1", ""), ("E", "endEvent", "End", 700, "L1", "")]
flows = [("f1", "S", "G1", "", None), ("f2", "G1", "A", "yes", "${c}"), ("f3", "G1", "B", "no", "${not c}"),
         ("f4", "A", "G2", "", None), ("f5", "B", "G2", "", None), ("f6", "G2", "E", "", None)]
build("deadlock_demo", "Deadlock example: XOR split and AND join", lanes, nodes, flows, "error-deadlock.bpmn")
