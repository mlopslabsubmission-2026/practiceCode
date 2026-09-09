from fastapi.testclient import TestClient
from main import app, accounts

client = TestClient(app)


def test_get_known_account():
    resp = client.get("/accounts/ACC1001")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Asha Rao"


def test_get_unknown_account_is_404():
    resp = client.get("/accounts/ACC9999")
    assert resp.status_code == 404


def test_debit_reduces_balance():
    before = accounts["ACC1001"]["balance"]
    resp = client.post("/accounts/ACC1001/debit", json={"amount": 100})
    assert resp.status_code == 200
    assert accounts["ACC1001"]["balance"] == before - 100


def test_debit_past_balance_is_rejected():
    resp = client.post("/accounts/ACC1003/debit", json={"amount": 999999})
    assert resp.status_code == 400


def test_credit_increases_balance():
    before = accounts["ACC1002"]["balance"]
    resp = client.post("/accounts/ACC1002/credit", json={"amount": 250})
    assert resp.status_code == 200
    assert accounts["ACC1002"]["balance"] == before + 250
