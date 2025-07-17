from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_get_trades():
    response = client.get("/trades")
    assert response.status_code == 200
    print("Payload:", response.json())
