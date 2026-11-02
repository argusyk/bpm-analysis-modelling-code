# Electronic Supplement to the Textbook "Fundamentals of Business Process Analysis and Modelling in IT"

Files for practicums 1–10 of Appendix G of the textbook. Everything is built on the running example of AeroCargo Service LLC.

| Folder | File | Purpose |
|---|---|---|
| models | aerocargo-asis.bpmn | "as-is" model (BPMN 2.0 with diagram), opens in Camunda Modeler and bpmn.io |
| models | aerocargo-tobe.bpmn | "to-be" model with parallel screening and customs clearance |
| models | error-deadlock.bpmn | deliberately erroneous model (deadlock) for exercises |
| models | make_bpmn.py | model generator (change and regenerate) |
| models | check_models.py | soundness check of the models via Petri nets and complexity metrics (Section 4.11.2) |
| decisions | handling-category.dmn | DMN decision table "Shipment handling category" |
| decisions | dmn_check.py | training decision table executor with tests |
| data | generate_log.py | generator of a synthetic event log of the "as-is" process |
| data | aerocargo_export_log.csv | log of 1,000 shipments (separator ";", UTF-8) |
| analysis | pm_analysis.py | process mining of the log with PM4Py |
| analysis | spc_chart.py | control chart of the average handling time (Section 7.10.2) |
| simulation | screening_sim.py | simulation model of the screening queue (SimPy), 4 scenarios |
| prozorro | build_log.py | building an event log from the open Prozorro API (Internet required), Section 9.1 |
| prozorro | analyze.py | process mining of the open tender log, results -> results.json |
| prozorro | prozorro_log.csv, prozorro_tenders.csv | log of 400 open tenders used in the textbook |
| camunda | README.md, worker.py | practicum on deployment in Camunda 8 (prepared according to the documentation, not run) |
| agent | awb_agent.py | LLM-based agent (Claude API), --offline mode without the network, Section 9.4 |
| security | sod_check.py | segregation-of-duties (SoD) check against an event log, Section 9.5 |
| ocel | build_ocel.py | object-centric purchasing log (OCEL 2.0), OC-DFG graph and consequences of flattening (Section 9.1.5) |
| iso | bpmn_to_procedure.py | generating a draft ISO 9001 procedure from a BPMN model, Section 10.2 |
| abc | abc_costing.py | activity-based costing (ABC), Section 10.3 |
| maturity | assessment.py | process management maturity self-assessment, Section 10.4 |

## Installation

Python 3.10 or later is required.

```
python -m venv .venv
.venv\Scripts\activate          (Windows)   |   source .venv/bin/activate   (Linux, macOS)
pip install -r requirements.txt   # pinned versions of pm4py, simpy, pandas, numpy
pip install anthropic      # only for a real run of the agent (requires the ANTHROPIC_API_KEY key)
pip install pyzeebe        # only for the Camunda 8 practicum
```

The PM4Py library is distributed under the AGPL v3 licence (free for teaching). SimPy: https://simpy.readthedocs.io.

## Procedure

```
python models/make_bpmn.py          # (optional) regenerate the models
python models/check_models.py       # soundness check
python decisions/dmn_check.py       # decision table tests
python data/generate_log.py 1000    # a new log (the seed is fixed)
python analysis/pm_analysis.py      # process mining
python analysis/spc_chart.py        # control chart
python simulation/screening_sim.py  # scenario simulation
python prozorro/build_log.py        # (Internet required) a new log from Prozorro
python prozorro/analyze.py          # analysis of the open tender log
python agent/awb_agent.py --offline # checking the agent loop without the network
python security/sod_check.py        # segregation-of-duties check
python ocel/build_ocel.py           # object-centric log
python iso/bpmn_to_procedure.py models/aerocargo-tobe.bpmn
python abc/abc_costing.py           # ABC calculation
python maturity/assessment.py       # maturity self-assessment
```

The programs overwrite the result files shipped with the supplement (results.json, CSV, procedure.md). To compare your run with the reference one, keep a copy of the folder before experimenting.

In the to-be model, waiting for the freight forwarder's reply is shown as the intermediate event "Correction received", while in the event log the same moment is recorded by the activity "Receive correction". In conformance checking pm_analysis.py considers only activities, so the model event and the log event "Cargo delivered" are not compared.

The log data are synthetic: they were generated with parameters consistent with Chapter 6 of the textbook and do not describe any real enterprise.

The Prozorro data are open data of the public procurement system; the results of the analysis depend on the sample and the time of download. In the English edition, the activity names of the Prozorro log have been translated into English; the original data are in Ukrainian. The agent in the agent folder uses the claude-opus-5 model with server-side fallback models enabled.
