# Listing from Section 9.4.2 of the textbook “Fundamentals of Business Process Analysis and Modelling in IT”.

def run_agent(client, awb, max_turns=8):
    messages = [{"role": "user", "content": f"Prepare shipment {awb} for acceptance."}]
    for _ in range(max_turns):
        resp = client.beta.messages.create(
            model="claude-opus-5", max_tokens=16000, system=SYSTEM, tools=TOOLS,
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
