# Лістинг з підрозділу 7.4.2 посібника «Основи аналізу та моделювання бізнес-процесів в ІТ».

import requests

resp = requests.post(
    "http://localhost:8080/v2/process-instances",
    json={
        "processDefinitionId": "export-shipment",      # ідентифікатор процесу з BPMN
        "variables": {
            "awb": "176-12345675",
            "shipper": "ТОВ Агроекспорт",
            "pieces": 12,
            "declaredWeightKg": 412,
            "flight": "PS781",
        },
    },
    timeout=10,
)
resp.raise_for_status()
print("створено екземпляр:", resp.json()["processInstanceKey"])
