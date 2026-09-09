from fastapi import FastAPI, Query

app = FastAPI(title="Fee Service")

MIN_FEE = 5.0
FEE_RATE = 0.005  # 0.5%


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/fee")
def get_fee(amount: float = Query(..., gt=0)):
    fee = max(MIN_FEE, round(amount * FEE_RATE, 2))
    return {"amount": amount, "fee": fee}
