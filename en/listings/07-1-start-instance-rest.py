# Listing from Section 7.4.2 of the textbook “Fundamentals of Business Process Analysis and Modelling in IT”.

import requests

resp = requests.post(
    "http://localhost:8080/v2/process-instances",
    json={
        "processDefinitionId": "export-shipment",      # process identifier from BPMN
        "variables": {
            "awb": "176-12345675",
            "shipper": "Agroexport LLC",
            "pieces": 12,
            "declaredWeightKg": 412,
            "flight": "PS781",
        },
    },
    timeout=10,
)
resp.raise_for_status()
print("instance created:", resp.json()["processInstanceKey"])
