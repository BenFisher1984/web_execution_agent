from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_activate_trade_stub():
    payload = {
        "trade": {
            "symbol": "AAPL",
            "qty": 10,
            "side": "buy",
            "order_type": "market",
            "price": None,
            "tif": "GTC"
        },
        "portfolio": {}
    }
    response = client.post("/activate_trade", json=payload)
    assert response.status_code == 200
    # optionally add more assertions
