import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Fund Transfer Service")

FEE_SERVICE_URL = os.environ.get("FEE_SERVICE_URL", "http://fee-service:8000")
ACCOUNT_SERVICE_URL = os.environ.get("ACCOUNT_SERVICE_URL", "http://account-service:8000")
JOURNAL_SERVICE_URL = os.environ.get("JOURNAL_SERVICE_URL", "http://journal-service:8000")


class TransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float = Field(gt=0)


async def _call(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> dict:
    """Call an atomic service and turn its errors into ours, instead of a raw 500."""
    resp = await client.request(method, url, **kwargs)
    if resp.status_code >= 400:
        detail = resp.json().get("detail", resp.text)
        raise HTTPException(status_code=resp.status_code, detail=f"{url}: {detail}")
    return resp.json()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/transfer")
async def transfer(req: TransferRequest):
    if req.from_account == req.to_account:
        raise HTTPException(status_code=400, detail="from_account and to_account must differ")

    async with httpx.AsyncClient(timeout=10) as client:
        # composite layer, step 1: what does this transfer cost?
        fee_result = await _call(client, "GET", f"{FEE_SERVICE_URL}/fee", params={"amount": req.amount})
        fee = fee_result["fee"]

        # step 2: take the amount + fee out of the sender
        await _call(
            client, "POST", f"{ACCOUNT_SERVICE_URL}/accounts/{req.from_account}/debit",
            json={"amount": req.amount + fee},
        )

        # step 3: put the amount into the receiver. If this fails, the sender
        # has already been debited — a real payments system needs a
        # compensating transaction (a saga) to put it back. This is that:
        try:
            await _call(
                client, "POST", f"{ACCOUNT_SERVICE_URL}/accounts/{req.to_account}/credit",
                json={"amount": req.amount},
            )
        except HTTPException:
            await _call(
                client, "POST", f"{ACCOUNT_SERVICE_URL}/accounts/{req.from_account}/credit",
                json={"amount": req.amount + fee},
            )
            raise HTTPException(status_code=502, detail="Transfer failed at credit step; sender refunded")

        # step 4: record what happened
        entry = await _call(
            client, "POST", f"{JOURNAL_SERVICE_URL}/journal",
            json={
                "from_account": req.from_account,
                "to_account": req.to_account,
                "amount": req.amount,
                "fee": fee,
                "status": "completed",
            },
        )

    return {"status": "completed", "fee": fee, "journal_entry": entry}
