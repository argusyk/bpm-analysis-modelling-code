# Лістинг з підрозділу 9.4.2 посібника «Основи аналізу та моделювання бізнес-процесів в ІТ».

def run_agent(client, awb, max_turns=8):
    messages = [{"role": "user", "content": f"Підготуй до приймання відправку {awb}."}]
    for _ in range(max_turns):
        resp = client.beta.messages.create(
            model="claude-opus-5", max_tokens=16000, system=SYSTEM, tools=TOOLS,
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
