# Лістинг з підрозділу 7.4.2 посібника «Основи аналізу та моделювання бізнес-процесів в ІТ».

import asyncio
from pyzeebe import ZeebeWorker, create_insecure_channel

worker = ZeebeWorker(create_insecure_channel(grpc_address="localhost:26500"))

@worker.task(task_type="validate-awb")
async def validate_awb(awb: str, pieces: int, declaredWeightKg: float) -> dict:
    errors = []
    if pieces <= 0:
        errors.append("кількість місць має бути додатною")
    if declaredWeightKg <= 0:
        errors.append("заявлена вага має бути додатною")
    # ... перевірка контрольної цифри номера AWB, кодів аеропортів, опису вантажу
    return {"awbValid": not errors, "awbErrors": errors}

asyncio.run(worker.work())
