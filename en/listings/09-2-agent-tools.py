# Listing from Section 9.4.2 of the textbook “Fundamentals of Business Process Analysis and Modelling in IT”.

TOOLS = [
    {"name": "validate_awb",
     "description": "Checks the e-AWB data against the terminal's rules and returns a list of errors.",
     "input_schema": {"type": "object", "properties": {"awb": {"type": "string"}},
                      "required": ["awb"]}},
    {"name": "confirm_slot",
     "description": "Confirms the delivery slot. Call only if validate_awb returned valid=true.",
     "input_schema": {"type": "object", "properties": {"awb": {"type": "string"}},
                      "required": ["awb"]}},
    # ... get_booking, request_correction, escalate_to_human
]
