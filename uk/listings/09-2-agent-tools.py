# Лістинг з підрозділу 9.4.2 посібника «Основи аналізу та моделювання бізнес-процесів в ІТ».

TOOLS = [
    {"name": "validate_awb",
     "description": "Перевіряє дані e-AWB за правилами терміналу і повертає перелік помилок.",
     "input_schema": {"type": "object", "properties": {"awb": {"type": "string"}},
                      "required": ["awb"]}},
    {"name": "confirm_slot",
     "description": "Підтверджує слот доставки. Викликати лише якщо validate_awb повернув valid=true.",
     "input_schema": {"type": "object", "properties": {"awb": {"type": "string"}},
                      "required": ["awb"]}},
    # ... get_booking, request_correction, escalate_to_human
]
