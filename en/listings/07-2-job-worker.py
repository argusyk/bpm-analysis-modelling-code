# Listing from Section 7.4.2 of the textbook “Fundamentals of Business Process Analysis and Modelling in IT”.

import asyncio
from pyzeebe import ZeebeWorker, create_insecure_channel

worker = ZeebeWorker(create_insecure_channel(grpc_address="localhost:26500"))

@worker.task(task_type="validate-awb")
async def validate_awb(awb: str, pieces: int, declaredWeightKg: float) -> dict:
    errors = []
    if pieces <= 0:
        errors.append("number of pieces must be positive")
    if declaredWeightKg <= 0:
        errors.append("declared weight must be positive")
    # ... check digit of the AWB number, airport codes, cargo description
    return {"awbValid": not errors, "awbErrors": errors}

asyncio.run(worker.work())
