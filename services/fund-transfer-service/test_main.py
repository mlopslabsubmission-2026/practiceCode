from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# This only tests validation that happens before any network call to the
# other three services. The full transfer flow is an integration test — it's
# exercised live via docker compose / Kubernetes during the practical, not
# here, since the atomic services aren't running under plain pytest.


def test_transfer_to_same_account_is_rejected():
    resp = client.post(
        "/transfer",
        json={"from_account": "ACC1001", "to_account": "ACC1001", "amount": 100},
    )
    assert resp.status_code == 400


def test_transfer_rejects_non_positive_amount():
    resp = client.post(
        "/transfer",
        json={"from_account": "ACC1001", "to_account": "ACC1002", "amount": 0},
    )
    assert resp.status_code == 422
