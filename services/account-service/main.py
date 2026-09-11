from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Account Service")

#Meera's balance is deliberately low
# so a debit past it demonstrates the insufficient-funds error path.
accounts = {
    "ACC1001": {"name": "Asha Rao", "balance": 5000.0},
    "ACC1002": {"name": "Vikram Shah", "balance": 12000.0},
    "ACC1003": {"name": "Meera Iyer", "balance": 800.0},
}


class AmountRequest(BaseModel):
    amount: float = Field(gt=0)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/accounts/{account_id}")
def get_account(account_id: str):
    account = accounts.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"No such account: {account_id}")
    return {"account_id": account_id, **account}


@app.post("/accounts/{account_id}/debit")
def debit(account_id: str, req: AmountRequest):
    account = accounts.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"No such account: {account_id}")
    if account["balance"] < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    account["balance"] -= req.amount
    return {"account_id": account_id, "balance": account["balance"]}


@app.post("/accounts/{account_id}/credit")
def credit(account_id: str, req: AmountRequest):
    account = accounts.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"No such account: {account_id}")
    account["balance"] += req.amount
    return {"account_id": account_id, "balance": account["balance"]}
