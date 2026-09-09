from datetime import datetime, timezone
from itertools import count

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Journal Service")

journal: list[dict] = []
_next_id = count(1)


class JournalEntry(BaseModel):
    from_account: str
    to_account: str
    amount: float
    fee: float
    status: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/journal")
def post_entry(entry: JournalEntry):
    record = {
        "entry_id": next(_next_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **entry.model_dump(),
    }
    journal.append(record)
    return record


@app.get("/journal")
def list_entries():
    return journal
