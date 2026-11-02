# -*- coding: utf-8 -*-
"""Self-assessment of process management maturity by the six core elements of BPM
(Rosemann, vom Brocke). Each statement is scored from 1 (not at all true) to 5
(completely true); the level of an element is the average score, the overall index is the average of the elements.
Run: python assessment.py [answers.json]  (an example of AeroCargo's answers is built in)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS = {
 "Strategic alignment": ["Processes are linked to the strategic goals of the organisation",
                             "Process improvement priorities are set using formal criteria",
                             "KPIs with target values are defined for key processes"],
 "Governance": ["Owners with authority have been appointed for key processes",
                              "There are rules for changing processes and models",
                              "Process indicators are regularly reviewed by management"],
 "Methods": ["The organisation uses a single modelling notation and style",
            "Quantitative methods are used to analyse processes",
            "Process improvements follow a defined cycle (BPM, DMAIC)"],
 "Information technology": ["Models are stored in a versioned repository",
                              "Key processes are executed or monitored by a system",
                              "Event logs are available for analysis (process mining)"],
 "People": ["Process analysts have appropriate training",
          "Performers understand their place in the end-to-end process",
          "Training in the process approach is part of employee onboarding"],
 "Culture": ["Process problems are discussed openly, without looking for someone to blame",
              "Employees propose improvements and see them implemented",
              "Decisions are made on the basis of process data"]}
EXAMPLE = {"Strategic alignment": [3, 3, 3], "Governance": [2, 1, 2], "Methods": [3, 2, 2],
           "Information technology": [2, 1, 1], "People": [2, 3, 2], "Culture": [3, 2, 2]}
TARGET = {"Strategic alignment": 4, "Governance": 3.5, "Methods": 3.5,
          "Information technology": 3.5, "People": 3, "Culture": 3}

answers = json.load(open(sys.argv[1], encoding="utf-8")) if len(sys.argv) > 1 else EXAMPLE
level = {e: round(sum(v) / len(v), 2) for e, v in answers.items()}
index = round(sum(level.values()) / len(level), 2)
gap = sorted(((round(TARGET[e] - level[e], 2), e) for e in level), reverse=True)
R = {"level": level, "index": index, "target": TARGET, "gaps": gap}
with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as _f:
    json.dump(R, _f, ensure_ascii=False, indent=1)
for e, v in level.items():
    print(f"{e:26s} {v:.2f}  (target {TARGET[e]})")
print("overall maturity index:", index)
print("largest gaps:", gap[:3])
