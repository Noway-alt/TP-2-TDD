from datetime import date
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.data import PROMO_CODES
from app.pricing import (
    PricingError,
    PromoNotFoundError,
    apply_promo_code,
    calculate_order_total,
)

app = FastAPI(title="API de tarification de livraison")

ORDERS: dict[str, dict] = {}  # stockage en mémoire


class Item(BaseModel):
    name: str
    price: float
    quantity: int


class OrderRequest(BaseModel):
    items: list[Item]
    distance: float
    weight: float
    promoCode: str | None = None
    hour: float
    dayOfWeek: str


class PromoRequest(BaseModel):
    code: str | None = None
    amount: float


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_request, exc):
    # Le sujet demande 400 (et non le 422 par défaut de FastAPI)
    errors = [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=400, content={"detail": "Requête invalide", "errors": errors})


def _compute(req: OrderRequest) -> dict:
    try:
        return calculate_order_total(
            items=[item.model_dump() for item in req.items],
            distance=req.distance,
            weight=req.weight,
            promo_code=req.promoCode,
            hour=req.hour,
            day_of_week=req.dayOfWeek,
            promo_codes=PROMO_CODES,
            today=date.today(),
        )
    except PricingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/orders/simulate")
def simulate_order(req: OrderRequest):
    return _compute(req)


@app.post("/orders", status_code=201)
def create_order(req: OrderRequest):
    pricing = _compute(req)  # si invalide : exception, rien n'est enregistré
    order_id = uuid4().hex
    order = {"id": order_id, "items": [i.model_dump() for i in req.items], **pricing}
    ORDERS[order_id] = order
    return order


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    order = ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    return order


@app.post("/promo/validate")
def validate_promo(req: PromoRequest):
    if not req.code:
        raise HTTPException(status_code=400, detail="Code promo requis")
    try:
        new_total = apply_promo_code(req.amount, req.code, PROMO_CODES, date.today())
    except PromoNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PricingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "valid": True,
        "code": req.code,
        "originalAmount": req.amount,
        "discount": round(req.amount - new_total, 2),
        "newTotal": new_total,
    }
