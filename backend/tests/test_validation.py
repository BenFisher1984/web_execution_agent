
from backend.services.validation import validate_trade


def test_valid_trade():
    trade = {
        "symbol": "AAPL",
        "direction": "buy",
        "entry_trigger": 200.0,
        "entry_rules": [{"primary_source": "Price", "condition": ">=", "secondary_source": "Custom", "value": 100}],
        "initial_stop_rules": [{"primary_source": "Price", "condition": "<=", "secondary_source": "Custom", "value": 90}],
        "trailing_stop_rules": [{"primary_source": "Price", "condition": "<=", "secondary_source": "EMA 8"}],
        "take_profit_rules": [{"primary_source": "Price", "condition": ">=", "secondary_source": "Custom", "value": 120}],
        "portfolio_value": 100000,
        "risk_pct": 1.0,
        "order_type": "market",
        "time_in_force": "GTC"
    }
    errors = validate_trade(trade)
    assert errors == [], f"Expected no errors, but got: {errors}"
    print("✅ test_valid_trade passed.")

def test_missing_fields():
    trade = {
        "symbol": "AAPL",
        "entry_trigger": 200.0,
        "portfolio_value": 100000,
        "risk_pct": 1.0
    }
    errors = validate_trade(trade)
    assert "Missing direction (e.g. 'buy' or 'sell')" in errors
    assert "Missing initial stop rule" in errors
    assert "Missing order type (e.g. 'market', 'limit')" in errors
    assert "Missing time in force (e.g. 'GTC')" in errors
    print("✅ test_missing_fields passed.")

if __name__ == "__main__":
    test_valid_trade()
    test_missing_fields()
