# Listing from Section 7.9.2 of the textbook “Fundamentals of Business Process Analysis and Modelling in IT”.

import json
import anthropic

client = anthropic.Anthropic()          # the key is taken from the ANTHROPIC_API_KEY variable
letter = open("shipper_instruction.txt", encoding="utf-8").read()

schema = {                               # air waybill fields
    "type": "object", "additionalProperties": False,
    "required": ["shipper", "consignee", "origin", "destination", "pieces",
                 "weight_kg", "description", "dangerous_goods"],
    "properties": {
        "shipper": {"type": ["string", "null"]},
        "consignee": {"type": ["string", "null"]},
        "origin": {"type": ["string", "null"]},
        "destination": {"type": ["string", "null"]},
        "pieces": {"type": ["integer", "null"]},
        "weight_kg": {"type": ["number", "null"]},
        "description": {"type": ["string", "null"]},
        "dangerous_goods": {"type": "boolean"}}}

resp = client.messages.create(
    model="claude-opus-5",
    max_tokens=16000,
    system=(
        "You assist a documentation agent at a cargo terminal. "
        "From the text of the shipper's instruction, extract the air waybill data. "
        "If data are missing, use null. Do not invent anything."
    ),
    messages=[{"role": "user", "content": letter}],
    output_config={"format": {"type": "json_schema", "schema": schema}},
)
if resp.stop_reason != "end_turn":      # a refusal or a truncated answer
    raise RuntimeError(f"hand over to the agent: {resp.stop_reason}")
text = next(b.text for b in resp.content if b.type == "text")   # a thinking block may come first
draft = json.loads(text)
print(draft)
