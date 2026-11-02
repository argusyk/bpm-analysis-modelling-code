# Лістинг з підрозділу 7.9.2 посібника «Основи аналізу та моделювання бізнес-процесів в ІТ».

import json
import anthropic

client = anthropic.Anthropic()          # ключ береться зі змінної ANTHROPIC_API_KEY
letter = open("shipper_instruction.txt", encoding="utf-8").read()

schema = {                               # поля авіанакладної
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
        "Ти допомагаєш агенту документації вантажного терміналу. "
        "З тексту інструкції відправника виділи дані для авіанакладної. "
        "Якщо даних немає, став null. Нічого не вигадуй."
    ),
    messages=[{"role": "user", "content": letter}],
    output_config={"format": {"type": "json_schema", "schema": schema}},
)
if resp.stop_reason != "end_turn":      # відмова моделі або обрізана відповідь
    raise RuntimeError(f"передати агенту вручну: {resp.stop_reason}")
text = next(b.text for b in resp.content if b.type == "text")   # перед ним може йти блок міркувань
draft = json.loads(text)
print(draft)
