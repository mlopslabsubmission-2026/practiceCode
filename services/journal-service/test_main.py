from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

SAMPLE_ENTRY = {
    "from_account": "ACC1001",
    "to_account": "ACC1002",
    "amount": 500,
    "fee": 5,
    "status": "completed",
}


def test_journal_starts_reachable():
    resp = client.get("/journal")
    assert resp.status_code == 200


def test_posting_an_entry_returns_it_with_an_id_and_timestamp():
    resp = client.post("/journal", json=SAMPLE_ENTRY)
    assert resp.status_code == 200
    body = resp.json()
    assert body["from_account"] == "ACC1001"
    assert "entry_id" in body
    assert "timestamp" in body


def test_posted_entries_show_up_in_the_listing():
    before = len(client.get("/journal").json())
    client.post("/journal", json=SAMPLE_ENTRY)
    after = client.get("/journal").json()
    assert len(after) == before + 1
