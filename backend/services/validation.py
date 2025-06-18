def validate_trade(trade: dict) -> list[str]:
    """
    Validates whether a trade contains all required fields to be activated.

    Returns:
        List of validation error messages. An empty list means the trade is valid.
    """
    errors = []

    # Required core fields
    if not trade.get("symbol"):
        errors.append("Missing symbol")

    if not trade.get("direction"):
        errors.append("Missing direction (e.g. 'buy' or 'sell')")

    if not trade.get("entry_trigger"):
        errors.append("Missing entry trigger price")

    if not trade.get("initial_stop_rule"):
        errors.append("Missing initial stop rule")
    else:
        stop_rule = trade["initial_stop_rule"]
        if stop_rule.get("type") == "custom" and stop_rule.get("price") is None:
            errors.append("Custom stop rule selected but no manual stop price provided")

    if not trade.get("portfolio_value"):
        errors.append("Missing portfolio value")

    if not trade.get("risk_pct"):
        errors.append("Missing risk % for trade sizing")

    if not trade.get("order_type"):
        errors.append("Missing order type (e.g. 'market', 'limit')")

    if not trade.get("time_in_force"):
        errors.append("Missing time in force (e.g. 'GTC')")

    # Trailing stop rule validation (based on GUI structure)
    trailing = trade.get("trailing_stop", {})
    if trailing.get("type") and trailing.get("price") is None:
        errors.append("Trailing stop type is set but no trailing stop price provided.")


    return errors
