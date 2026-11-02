# -*- coding: utf-8 -*-
"""A minimal DMN decision table executor for self-checking (for teaching).
Supports a subset of FEEL in cells: '-', not(null), strings and lists of strings,
comparisons (<, <=, >, >=) and ranges [a..b] for numbers; the FIRST and UNIQUE policies.
Run: python dmn_check.py  (runs the test sets from the practicum table)"""
import os, re, xml.etree.ElementTree as ET

NS = {"d": "https://www.omg.org/spec/DMN/20191111/MODEL/"}
HERE = os.path.dirname(os.path.abspath(__file__))


def load(path):
    root = ET.parse(path).getroot()
    dt = root.find(".//d:decisionTable", NS)
    inputs = [i.find("d:inputExpression/d:text", NS).text.strip() for i in dt.findall("d:input", NS)]
    outputs = [o.get("name") for o in dt.findall("d:output", NS)]
    rules = []
    for r in dt.findall("d:rule", NS):
        ins = [e.find("d:text", NS).text.strip() for e in r.findall("d:inputEntry", NS)]
        outs = [e.find("d:text", NS).text.strip() for e in r.findall("d:outputEntry", NS)]
        rules.append((r.get("id"), ins, outs))
    return dt.get("hitPolicy", "UNIQUE"), inputs, outputs, rules


def match(cell, value):
    if cell == "-":
        return True
    if cell == "not(null)":
        return value is not None
    if cell == "null":
        return value is None
    if cell.startswith('"'):
        return value in (re.findall(r'"([^"]*)"', cell) or [s.strip() for s in cell.split(",")])
    m = re.fullmatch(r"(<=|>=|<|>)\s*(-?\d+(?:\.\d+)?)", cell)
    if m and value is not None:
        op, x = m.group(1), float(m.group(2))
        return {"<": value < x, "<=": value <= x, ">": value > x, ">=": value >= x}[op]
    m = re.fullmatch(r"\[(-?\d+(?:\.\d+)?)\.\.(-?\d+(?:\.\d+)?)\]", cell)
    if m and value is not None:
        return float(m.group(1)) <= value <= float(m.group(2))
    raise ValueError(f"unsupported FEEL expression: {cell}")


def literal(t):
    if t in ("true", "false"):
        return t == "true"
    if t.startswith('"'):
        return t.strip('"')
    return float(t)


def evaluate(table, data):
    policy, inputs, outputs, rules = table
    hits = [(rid, outs) for rid, ins, outs in rules if all(match(c, data.get(k)) for c, k in zip(ins, inputs))]
    if policy == "UNIQUE" and len(hits) > 1:
        raise ValueError(f"UNIQUE policy violated: rules fired {[h[0] for h in hits]}")
    if not hits:
        return None, {}
    rid, outs = hits[0]
    return rid, {o: literal(v) for o, v in zip(outputs, outs)}


if __name__ == "__main__":
    table = load(os.path.join(HERE, "handling-category.dmn"))
    tests = [
        ({"dgClass": "3", "tempRange": None, "declaredValueUsd": 1200}, "DG"),
        ({"dgClass": None, "tempRange": "2-8C", "declaredValueUsd": 80000}, "COL"),
        ({"dgClass": None, "tempRange": None, "declaredValueUsd": 50000}, "VAL"),
        ({"dgClass": None, "tempRange": None, "declaredValueUsd": 49999}, "STD"),
        ({"dgClass": "9", "tempRange": "2-8C", "declaredValueUsd": 90000}, "DG"),
    ]
    ok = 0
    for data, expected in tests:
        rid, res = evaluate(table, data)
        mark = "OK " if res.get("category") == expected else "FAIL"
        ok += mark == "OK "
        print(f"{mark} {data} -> rule {rid}: {res}")
    print(f"passed {ok} of {len(tests)} tests")
