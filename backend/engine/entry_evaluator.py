# backend/engine/entry_evaluator.py

class EntryEvaluator:
    """
    Handles entry evaluation including direction.
    """

    def evaluate_entry(self, trade: dict, last_price: float) -> bool:
        """
        Evaluate if a trade should be activated.

        Supports:
        - Long: last_price >= rule_price
        - Short: last_price <= rule_price

        Ignores user-configured entry_condition for safety.
        """

        entry_rule = trade.get("entry_rule", "Custom")
        entry_rule_price = trade.get("entry_rule_price")
        direction = trade.get("direction", "Long")

        # fallback
        if entry_rule_price is None:
            entry_rule_price = trade.get("entry_trigger")

        if entry_rule != "Custom":
            # placeholder for future logic
            return False

        if direction == "Long":
            return last_price >= entry_rule_price
        elif direction == "Short":
            return last_price <= entry_rule_price
        else:
            return False
