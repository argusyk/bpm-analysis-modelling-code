# -*- coding: utf-8 -*-
"""An agent based on a language model that performs the AeroCargo process service task
"Prepare the shipment for acceptance": it reads the booking, checks the e-AWB data
with tools and decides whether to confirm the slot, request a correction or hand the case
over to a person. The agent does not make decisions with a high cost of error itself (human in the loop).

Modes:
  python awb_agent.py --offline   – check the agent loop without the network (scripted model)
  python awb_agent.py             – a real Claude API call (requires the ANTHROPIC_API_KEY key
                                    or an `ant auth login` profile; pip install anthropic)"""
import json, re, sys
from types import SimpleNamespace as NS

MODEL = "claude-opus-5"

# ---------- data and tools (in a real system – service calls) ----------
BOOKINGS = {
    "176-12345675": {"awb": "176-12345675", "pieces": 12, "weight_kg": 412, "origin": "KBP", "destination": "WAW",
                     "description": "spare parts for agricultural machinery", "dangerous_goods": None},
    "176-12345674": {"awb": "176-12345674", "pieces": 3, "weight_kg": 0, "origin": "KBP", "destination": "FRA",
                     "description": "", "dangerous_goods": None},
    "176-12345686": {"awb": "176-12345686", "pieces": 4, "weight_kg": 96, "origin": "KBP", "destination": "AMS",
                     "description": "lithium-ion batteries for e-scooters", "dangerous_goods": None},
}

def get_booking(awb):
    return BOOKINGS.get(awb) or {"error": f"booking {awb} not found"}

def validate_awb(awb):
    b = BOOKINGS.get(awb)
    if not b:
        return {"valid": False, "errors": ["booking not found"]}
    errors = []
    serial = awb.split("-")[1]
    if int(serial[:7]) % 7 != int(serial[7]):
        errors.append("invalid check digit of the AWB number")
    if b["weight_kg"] <= 0:
        errors.append("weight must be positive")
    if not b["description"]:
        errors.append("cargo description is missing")
    if not errors:
        VALIDATED.add(awb)
    return {"valid": not errors, "errors": errors}

ACTIONS, VALIDATED = [], set()
def confirm_slot(awb):
    # the condition from the tool description is enforced in code: the model's description is not enough
    if awb not in VALIDATED:
        return {"error": "slot not confirmed: a successful validate_awb check is required first"}
    ACTIONS.append(("confirm_slot", awb)); return {"status": "delivery slot confirmed"}

def request_correction(awb, errors):
    ACTIONS.append(("request_correction", awb, errors)); return {"status": "request for correction sent to the freight forwarder"}

def escalate_to_human(awb, reason):
    ACTIONS.append(("escalate_to_human", awb, reason)); return {"status": "a task has been created for a documentation agent"}

HANDLERS = {"get_booking": get_booking, "validate_awb": validate_awb, "confirm_slot": confirm_slot,
            "request_correction": request_correction, "escalate_to_human": escalate_to_human}

def obj(props, req):
    return {"type": "object", "properties": props, "required": req, "additionalProperties": False}
AWB = {"awb": {"type": "string", "description": "air waybill number in the format 176-12345675"}}
TOOLS = [
    {"name": "get_booking", "description": "Returns the booking and e-AWB data for an air waybill number.", "input_schema": obj(AWB, ["awb"])},
    {"name": "validate_awb", "description": "Checks the e-AWB data against the terminal's rules and returns a list of errors.", "input_schema": obj(AWB, ["awb"])},
    {"name": "confirm_slot", "description": "Confirms the delivery slot. Call only if validate_awb returned valid=true.", "input_schema": obj(AWB, ["awb"])},
    {"name": "request_correction", "description": "Sends the freight forwarder a request for correction with a list of errors.",
     "input_schema": obj({**AWB, "errors": {"type": "array", "items": {"type": "string"}}}, ["awb", "errors"])},
    {"name": "escalate_to_human", "description": "Hands the case over to a documentation agent if the decision is not obvious or the cargo may be dangerous.",
     "input_schema": obj({**AWB, "reason": {"type": "string"}}, ["awb", "reason"])},
]
SYSTEM = ("You perform a service task of the export shipment handling process at a cargo terminal. "
          "For each shipment: get the booking, check the e-AWB data, and then either confirm the delivery slot "
          "or request a correction with an exact list of errors. If the cargo description points to possible dangerous goods "
          "or the data are contradictory, hand the case over to a person via escalate_to_human. At the end, briefly summarise the decision.")

# ---------- agent loop ----------
def run_agent(client, awb, max_turns=8):
    messages = [{"role": "user", "content": f"Prepare shipment {awb} for acceptance."}]
    for _ in range(max_turns):
        resp = client.beta.messages.create(model=MODEL, max_tokens=16000, system=SYSTEM, tools=TOOLS,
                                           messages=messages, betas=["server-side-fallback-2026-07-01"],
                                           extra_body={"fallbacks": "default"})
        if resp.stop_reason == "refusal":
            return escalate_to_human(awb, "the model refused to process the request")["status"]
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
                except Exception as e:      # unknown tool or invalid arguments
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": f"error: {e}", "is_error": True})
        messages.append({"role": "user", "content": results})
    return escalate_to_human(awb, "agent step limit exceeded")["status"]

# ---------- scripted model for checking without the network ----------
class ScriptedClient:
    """Imitates the model's responses: calls the tools in the typical order and reacts to the result of the check."""
    def __init__(self):
        self.beta = NS(messages=NS(create=self.create))
    def create(self, **kw):
        msgs = kw["messages"]
        awb = re.search(r"\d{3}-\d{8}",msgs[0]["content"]).group()
        step = sum(1 for m in msgs if m["role"] == "assistant")
        tu = lambda name, inp, n: NS(type="tool_use", id=f"tu_{n}", name=name, input=inp)
        if step == 0:
            return NS(stop_reason="tool_use", content=[tu("get_booking", {"awb": awb}, 0)])
        if step == 1:
            booking = json.loads(msgs[-1]["content"][0]["content"])
            if "batter" in booking.get("description", ""):   # possibly dangerous goods
                return NS(stop_reason="tool_use", content=[tu("escalate_to_human", {"awb": awb,
                          "reason": "the description points to possible dangerous goods (lithium batteries)"}, 1)])
            return NS(stop_reason="tool_use", content=[tu("validate_awb", {"awb": awb}, 1)])
        if step == 2 and kw["messages"][-2]["content"][0].name == "validate_awb":
            check = json.loads(msgs[-1]["content"][0]["content"])
            if check["valid"]:
                return NS(stop_reason="tool_use", content=[tu("confirm_slot", {"awb": awb}, 2)])
            return NS(stop_reason="tool_use", content=[tu("request_correction", {"awb": awb, "errors": check["errors"]}, 2)])
        return NS(stop_reason="end_turn", content=[NS(type="text", text=f"Shipment {awb} has been processed.")])

if __name__ == "__main__":
    if "--offline" in sys.argv:
        client = ScriptedClient()
    else:
        import anthropic
        client = anthropic.Anthropic()
    for awb in BOOKINGS:
        print(awb, "->", run_agent(client, awb))
    print("agent actions:")
    for a in ACTIONS:
        print("  ", a)
