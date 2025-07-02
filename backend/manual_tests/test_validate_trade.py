import requests

response = requests.post("http://localhost:8000/validate_trade", json={
    "trade": {
        "symbol": "AAPL",
        "risk_pct": 1,
        "direction": "long",
        "time_in_force": "GTC",
        "order_type": "market",
        "entry_trigger": 190,
        "initial_stop_rule": {"type": "stop_loss", "price": 180}
    },
    "portfolio": {"value": 100000}
})

print("Status code:", response.status_code)
print("Response JSON:", response.json())
