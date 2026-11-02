# -*- coding: utf-8 -*-
"""Агент на основі мовної моделі, що виконує сервісну задачу процесу АероКарго
«Підготувати відправку до приймання»: читає бронювання, перевіряє дані e-AWB
інструментами і вирішує – підтвердити слот, запросити виправлення чи передати
людині. Рішення з високою ціною помилки агент не ухвалює сам (людина в контурі).

Режими:
  python awb_agent.py --offline   – перевірка циклу агента без мережі (сценарна модель)
  python awb_agent.py             – реальний виклик Claude API (потрібен ключ ANTHROPIC_API_KEY
                                    або профіль `ant auth login`; pip install anthropic)"""
import json, sys
from types import SimpleNamespace as NS

MODEL = "claude-opus-5"

# ---------- дані й інструменти (у реальній системі – виклики сервісів) ----------
BOOKINGS = {
    "176-12345675": {"awb": "176-12345675", "pieces": 12, "weight_kg": 412, "origin": "KBP", "destination": "WAW",
                     "description": "запасні частини до сільгосптехніки", "dangerous_goods": None},
    "176-12345674": {"awb": "176-12345674", "pieces": 3, "weight_kg": 0, "origin": "KBP", "destination": "FRA",
                     "description": "", "dangerous_goods": None},
    "176-12345686": {"awb": "176-12345686", "pieces": 4, "weight_kg": 96, "origin": "KBP", "destination": "AMS",
                     "description": "літій-іонні акумулятори для електросамокатів", "dangerous_goods": None},
}

def get_booking(awb):
    return BOOKINGS.get(awb) or {"error": f"бронювання {awb} не знайдено"}

def validate_awb(awb):
    b = BOOKINGS.get(awb)
    if not b:
        return {"valid": False, "errors": ["бронювання не знайдено"]}
    errors = []
    serial = awb.split("-")[1]
    if int(serial[:7]) % 7 != int(serial[7]):
        errors.append("невірна контрольна цифра номера AWB")
    if b["weight_kg"] <= 0:
        errors.append("вага має бути додатною")
    if not b["description"]:
        errors.append("відсутній опис вантажу")
    if not errors:
        VALIDATED.add(awb)
    return {"valid": not errors, "errors": errors}

ACTIONS, VALIDATED = [], set()
def confirm_slot(awb):
    # умову з опису інструмента перевіряє код: на опис для моделі покладатися не можна
    if awb not in VALIDATED:
        return {"error": "слот не підтверджено: спершу потрібна успішна перевірка validate_awb"}
    ACTIONS.append(("confirm_slot", awb)); return {"status": "слот доставки підтверджено"}

def request_correction(awb, errors):
    ACTIONS.append(("request_correction", awb, errors)); return {"status": "запит на виправлення надіслано експедитору"}

def escalate_to_human(awb, reason):
    ACTIONS.append(("escalate_to_human", awb, reason)); return {"status": "створено задачу для агента документації"}

HANDLERS = {"get_booking": get_booking, "validate_awb": validate_awb, "confirm_slot": confirm_slot,
            "request_correction": request_correction, "escalate_to_human": escalate_to_human}

def obj(props, req):
    return {"type": "object", "properties": props, "required": req, "additionalProperties": False}
AWB = {"awb": {"type": "string", "description": "номер авіанакладної у форматі 176-12345675"}}
TOOLS = [
    {"name": "get_booking", "description": "Повертає дані бронювання і e-AWB за номером авіанакладної.", "input_schema": obj(AWB, ["awb"])},
    {"name": "validate_awb", "description": "Перевіряє дані e-AWB за правилами терміналу і повертає перелік помилок.", "input_schema": obj(AWB, ["awb"])},
    {"name": "confirm_slot", "description": "Підтверджує слот доставки. Викликати лише якщо validate_awb повернув valid=true.", "input_schema": obj(AWB, ["awb"])},
    {"name": "request_correction", "description": "Надсилає експедитору запит на виправлення з переліком помилок.",
     "input_schema": obj({**AWB, "errors": {"type": "array", "items": {"type": "string"}}}, ["awb", "errors"])},
    {"name": "escalate_to_human", "description": "Передає випадок агенту документації, якщо рішення неочевидне або вантаж може бути небезпечним.",
     "input_schema": obj({**AWB, "reason": {"type": "string"}}, ["awb", "reason"])},
]
SYSTEM = ("Ти виконуєш сервісну задачу процесу обробки експортних відправок вантажного терміналу. "
          "Для кожної відправки: отримай бронювання, перевір дані e-AWB, а потім або підтверди слот доставки, "
          "або запроси виправлення з точним переліком помилок. Якщо опис вантажу вказує на можливий небезпечний вантаж "
          "або дані суперечливі, передай випадок людині через escalate_to_human. Наприкінці коротко підсумуй рішення.")

# ---------- цикл агента ----------
def run_agent(client, awb, max_turns=8):
    messages = [{"role": "user", "content": f"Підготуй до приймання відправку {awb}."}]
    for _ in range(max_turns):
        resp = client.beta.messages.create(model=MODEL, max_tokens=16000, system=SYSTEM, tools=TOOLS,
                                           messages=messages, betas=["server-side-fallback-2026-07-01"],
                                           extra_body={"fallbacks": "default"})
        if resp.stop_reason == "refusal":
            return escalate_to_human(awb, "модель відмовилася обробляти запит")["status"]
        if resp.stop_reason != "tool_use":
            return next((b.text for b in resp.content if b.type == "text"), "")
        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                try:
                    out = HANDLERS[block.name](**block.input)
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": json.dumps(out, ensure_ascii=False)})
                except Exception as e:      # невідомий інструмент або хибні аргументи
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": f"помилка: {e}", "is_error": True})
        messages.append({"role": "user", "content": results})
    return escalate_to_human(awb, "перевищено ліміт кроків агента")["status"]

# ---------- сценарна модель для перевірки без мережі ----------
class ScriptedClient:
    """Імітує відповіді моделі: викликає інструменти в типовому порядку і реагує на результат перевірки."""
    def __init__(self):
        self.beta = NS(messages=NS(create=self.create))
    def create(self, **kw):
        msgs = kw["messages"]
        awb = msgs[0]["content"].split()[-1].rstrip(".")
        step = sum(1 for m in msgs if m["role"] == "assistant")
        tu = lambda name, inp, n: NS(type="tool_use", id=f"tu_{n}", name=name, input=inp)
        if step == 0:
            return NS(stop_reason="tool_use", content=[tu("get_booking", {"awb": awb}, 0)])
        if step == 1:
            booking = json.loads(msgs[-1]["content"][0]["content"])
            if "акумулятор" in booking.get("description", ""):   # можливий небезпечний вантаж
                return NS(stop_reason="tool_use", content=[tu("escalate_to_human", {"awb": awb,
                          "reason": "опис вказує на можливий небезпечний вантаж (літієві батареї)"}, 1)])
            return NS(stop_reason="tool_use", content=[tu("validate_awb", {"awb": awb}, 1)])
        if step == 2 and kw["messages"][-2]["content"][0].name == "validate_awb":
            check = json.loads(msgs[-1]["content"][0]["content"])
            if check["valid"]:
                return NS(stop_reason="tool_use", content=[tu("confirm_slot", {"awb": awb}, 2)])
            return NS(stop_reason="tool_use", content=[tu("request_correction", {"awb": awb, "errors": check["errors"]}, 2)])
        return NS(stop_reason="end_turn", content=[NS(type="text", text=f"Відправку {awb} оброблено.")])

if __name__ == "__main__":
    if "--offline" in sys.argv:
        client = ScriptedClient()
    else:
        import anthropic
        client = anthropic.Anthropic()
    for awb in BOOKINGS:
        print(awb, "->", run_agent(client, awb))
    print("дії агента:")
    for a in ACTIONS:
        print("  ", a)
