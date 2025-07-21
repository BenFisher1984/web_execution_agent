import json
import os
from jsonschema import validate as schema_validate, ValidationError
from pathlib import Path

# Load the layout_config at module load
LAYOUT_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "layout_config.json")
with open(LAYOUT_PATH, "r") as f:
    layout_config = json.load(f)

def get_mandatory_fields_from_layout():
    """
    Extract all keys marked as mandatory in layout_config.json
    """
    fields = []
    for section in layout_config:
        for field in section.get("fields", []):
            if field.get("mandatory") is True:
                fields.append(field["key"])
    return fields

def get_nested_field(data, key):
    """
    Supports dot-notation keys, e.g. volatility.adr_20 and array indexes like entry_rules.0.value
    """
    try:
        if "." not in key:
            return data.get(key)
        for part in key.split("."):
            if isinstance(data, dict):
                data = data.get(part)
            elif isinstance(data, list):
                # Handle array indexes
                if part.isdigit():
                    index = int(part)
                    if 0 <= index < len(data):
                        data = data[index]
                    else:
                        return None
                else:
                    return None
            else:
                return None
        return data
    except Exception:
        return None

def validate_editing_status_consistency(trade: dict) -> dict:
    """
    Validates that editing field is consistent with order/trade status.
    Business rule: editing=true should only exist with no status fields or Draft status.
    """
    editing = trade.get("editing", False)
    order_status = trade.get("order_status")
    trade_status = trade.get("trade_status")
    
    # If editing=true, status fields should be empty/null or Draft
    if editing:
        if order_status and order_status != "Draft":
            return {"valid": False, "reason": f"Inconsistent state: editing=true but order_status='{order_status}'. Active trades cannot be in editing mode."}
        if trade_status and trade_status not in [None, "", "Draft"]:
            return {"valid": False, "reason": f"Inconsistent state: editing=true but trade_status='{trade_status}'. Active trades cannot be in editing mode."}
    
    # If status indicates active trade, editing must be false
    active_order_statuses = ["Working", "Entry Order Submitted", "Contingent Order Submitted", "Contingent Order Working"]
    active_trade_statuses = ["Pending", "Filled"]
    
    if order_status in active_order_statuses and editing:
        return {"valid": False, "reason": f"Inconsistent state: order_status='{order_status}' requires editing=false"}
    
    if trade_status in active_trade_statuses and editing:
        return {"valid": False, "reason": f"Inconsistent state: trade_status='{trade_status}' requires editing=false"}
    
    return {"valid": True}

def validate_trade(trade: dict, portfolio: dict = None) -> dict:
    try:
        print("🚦 validate_trade called with trade:")
        print(json.dumps(trade, indent=2))
        
        # First check editing/status consistency
        consistency_check = validate_editing_status_consistency(trade)
        if not consistency_check["valid"]:
            return consistency_check
        
        # Validate against schema if available
        schema_path = Path(__file__).parent.parent / "schemas" / "trade_schema.json"
        if schema_path.exists():
            with open(schema_path) as f:
                trade_schema = json.load(f)

            print(f"🔍 DEBUG TRADE PAYLOAD:\n{json.dumps(trade, indent=2)}")

            try:
                schema_validate(instance=trade, schema=trade_schema)
            except ValidationError as e:
                return {"valid": False, "reason": f"Schema validation error: {e.message}"}

        # Validate all mandatory fields from layout_config
        mandatory_fields = get_mandatory_fields_from_layout()
        for field in mandatory_fields:
            value = get_nested_field(trade, field)
            print(f"🧪 Checking mandatory field: {field} → {value}")
            if value in [None, ""]:
                return {"valid": False, "reason": f"Missing required field: {field}"}

        # Future portfolio checks could go here if needed
        # for now, we omit them for simplicity

        return {"valid": True}

    except Exception as e:
        return {"valid": False, "reason": f"Validation error: {str(e)}"}
