# -*- coding: utf-8 -*-
"""Зовнішній виконавець (job worker) для сервісної задачі validate-awb у Camunda 8.
Не запускався в середовищі підготовки посібника (див. README.md). pip install pyzeebe"""
import asyncio
import re
from pyzeebe import ZeebeWorker, create_insecure_channel

worker = ZeebeWorker(create_insecure_channel(grpc_address="localhost:26500"))


@worker.task(task_type="validate-awb")
async def validate_awb(awb: str, pieces: int = 0, declaredWeightKg: float = 0) -> dict:
    if not re.fullmatch(r"\d{3}-\d{8}", awb or ""):
        return {"awbValid": False, "awbErrors": ["невірний формат номера AWB"]}
    errors = []
    serial = awb.split("-")[1]
    if int(serial[:7]) % 7 != int(serial[7]):
        errors.append("невірна контрольна цифра номера AWB")
    if pieces <= 0:
        errors.append("кількість місць має бути додатною")
    if declaredWeightKg <= 0:
        errors.append("заявлена вага має бути додатною")
    return {"awbValid": not errors, "awbErrors": errors}


if __name__ == "__main__":
    asyncio.run(worker.work())
