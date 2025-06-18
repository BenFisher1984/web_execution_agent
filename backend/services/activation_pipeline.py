
from backend.services.validation import validate_trade


def calculate_position_size(trade: dict) -> int:
    """
    Calculates trade quantity based on portfolio risk and stop distance.

    Formula:
        position_size = (portfolio_value * risk_pct) / (entry_trigger - stop_price)

    Returns:
        Integer number of shares to trade.
    """
    try:
        trigger_price = trade["entry_trigger"]
        stop_rule = trade.get("initial_stop_rule", {})
        stop_price = stop_rule.get("price") if stop_rule.get("type") == "custom" else None

        if stop_price is None:
            raise ValueError("Stop price not defined or unsupported rule type")

        stop_distance = trigger_price - stop_price
        if stop_distance <= 0:
            raise ValueError("Invalid stop distance: must be positive")

        portfolio_value = trade["portfolio_value"]
        risk_pct = trade["risk_pct"]
        risk_dollars = portfolio_value * (risk_pct / 100)

        position_size = int(risk_dollars / stop_distance)
        return max(position_size, 0)

    except Exception as e:
        print(f"❌ Failed to calculate position size: {e}")
        return 0


def activate_trade(trade: dict) -> tuple[bool, list[str]]:
    """
    Validates and activates a trade.
    If validation passes, calculates position size and sets status to active.

    Returns:
        (success: bool, errors: list[str])
    """
    errors = validate_trade(trade)
    if errors:
        return False, errors

    qty = calculate_position_size(trade)
    trade["quantity"] = qty
    trade["order_status"] = "active"
    return True, []
