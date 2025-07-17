import requests

test_trade = {
    "symbol": "AAPL",
    "risk_pct": 1,
    "direction": "long",
    "time_in_force": "GTC",
    "order_type": "market",
    "entry_trigger": 190,
    "entry_rules": [{"primary_source": "Custom", "condition": ">=", "secondary_source": "Custom", "value": 100}],
    "initial_stop_rules": [{"primary_source": "Price", "condition": "<=", "secondary_source": "Custom", "value": 90}],
    "trailing_stop_rules": [{"primary_source": "Price", "condition": "<=", "secondary_source": "EMA 8"}],
    "take_profit_rules": [{"primary_source": "Price", "condition": ">=", "secondary_source": "Custom", "value": 120}]
}

response = requests.post("http://localhost:8000/validate_trade", json={
    "trade": test_trade,
    "portfolio": {"value": 100000}
})

print("Status code:", response.status_code)
print("Response JSON:", response.json())
