from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_fee_uses_minimum_for_small_amounts():
    resp = client.get("/fee", params={"amount": 100})
    assert resp.status_code == 200
    assert resp.json()["fee"] == 5.0  # 0.5% of 100 is 0.50, below the ₹5 minimum


def test_fee_uses_percentage_for_large_amounts():
    resp = client.get("/fee", params={"amount": 10000})
    assert resp.json()["fee"] == 50.0  # 0.5% of 10000


def test_fee_rejects_non_positive_amount():
    resp = client.get("/fee", params={"amount": 0})
    assert resp.status_code == 422
