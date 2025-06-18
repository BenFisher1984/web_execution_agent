
from backend.services.activation_pipeline import activate_trade

def test_activate_trade_valid():
    trade = {
        "symbol": "AAPL",
        "direction": "buy",
        "entry_trigger": 200.0,
        "initial_stop_rule": {
            "type": "custom",
            "price": 190.0
        },
        "portfolio_value": 100000,
        "risk_pct": 1.0,
        "order_type": "market",
        "time_in_force": "GTC"
    }

    success, errors = activate_trade(trade)

    assert success is True, f"Expected success but got errors: {errors}"
    assert "quantity" in trade and trade["quantity"] > 0, "Quantity not set correctly"
    assert trade["order_status"] == "active", "Trade status not set to active"
    print(f"📦 Calculated quantity: {trade['quantity']}")
    print("✅ test_activate_trade_valid passed.")

def test_activate_trade_invalid():
    trade = {
        "symbol": "AAPL",
        "entry_trigger": 200.0,
        "portfolio_value": 100000,
        "risk_pct": 1.0
    }

    success, errors = activate_trade(trade)

    assert success is False, "Expected failure due to missing fields"
    assert isinstance(errors, list) and len(errors) > 0, "Expected list of validation errors"
    print("✅ test_activate_trade_invalid passed.")

if __name__ == "__main__":
    test_activate_trade_valid()
    test_activate_trade_invalid()
