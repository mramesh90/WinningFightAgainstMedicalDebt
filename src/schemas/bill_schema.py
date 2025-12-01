"""
Schema definitions for medical bill data structures.
"""

BILL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "patient_name": {"type": "STRING"},
        "account_number": {"type": "STRING"},
        "statement_date": {"type": "STRING"},
        "provider_name": {"type": "STRING", "nullable": True},
        "line_items": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "date": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "cpt_code": {"type": "STRING", "nullable": True},
                    "amount_charged": {"type": "NUMBER"}
                }
            }
        },
        "total_amount": {"type": "NUMBER"}
    },
    "required": ["line_items", "total_amount"]
}

