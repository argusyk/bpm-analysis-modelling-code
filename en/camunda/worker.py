# -*- coding: utf-8 -*-
"""External job worker for the validate-awb service task in Camunda 8.
Not run in the environment where the book was prepared (see README.md). pip install pyzeebe"""
import asyncio
import re
from pyzeebe import ZeebeWorker, create_insecure_channel

worker = ZeebeWorker(create_insecure_channel(grpc_address="localhost:26500"))


@worker.task(task_type="validate-awb")
async def validate_awb(awb: str, pieces: int = 0, declaredWeightKg: float = 0) -> dict:
    if not re.fullmatch(r"\d{3}-\d{8}", awb or ""):
        return {"awbValid": False, "awbErrors": ["invalid AWB number format"]}
    errors = []
    serial = awb.split("-")[1]
    if int(serial[:7]) % 7 != int(serial[7]):
        errors.append("invalid check digit of the AWB number")
    if pieces <= 0:
        errors.append("number of pieces must be positive")
    if declaredWeightKg <= 0:
        errors.append("declared weight must be positive")
    return {"awbValid": not errors, "awbErrors": errors}


if __name__ == "__main__":
    asyncio.run(worker.work())
