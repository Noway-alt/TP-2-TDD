import pytest

from app.main import ORDERS


def make_payload(**overrides):
    payload = {
        "items": [{"name": "Pizza", "price": 12.5, "quantity": 2}],
        "distance": 5,
        "weight": 2,
        "promoCode": None,
        "hour": 15,
        "dayOfWeek": "tuesday",
    }
    payload.update(overrides)
    return payload


# =============== POST /orders/simulate ===============
def test_simulate_should_return_200_and_correct_price_for_normal_order(client):
    response = client.post("/orders/simulate", json=make_payload())
    assert response.status_code == 200
    assert response.json() == {
        "subtotal": 25.0,
        "discount": 0.0,
        "deliveryFee": 3.0,
        "surge": 1.0,
        "total": 28.0,
    }


def test_simulate_should_apply_valid_promo_code(client):
    response = client.post("/orders/simulate", json=make_payload(promoCode="BIENVENUE20"))
    assert response.status_code == 200
    assert response.json()["discount"] == 5.0
    assert response.json()["total"] == 23.0


def test_simulate_should_return_400_when_promo_is_expired(client):
    response = client.post("/orders/simulate", json=make_payload(promoCode="VIEUX10"))
    assert response.status_code == 400
    assert "expir" in response.json()["detail"].lower()


def test_simulate_should_return_400_when_basket_is_empty(client):
    response = client.post("/orders/simulate", json=make_payload(items=[]))
    assert response.status_code == 400


def test_simulate_should_return_400_when_out_of_zone(client):
    response = client.post("/orders/simulate", json=make_payload(distance=15))
    assert response.status_code == 400


def test_simulate_should_return_400_when_closed(client):
    response = client.post("/orders/simulate", json=make_payload(hour=23))
    assert response.status_code == 400


def test_simulate_should_multiply_delivery_fee_on_friday_evening(client):
    response = client.post("/orders/simulate", json=make_payload(hour=20, dayOfWeek="friday"))
    assert response.status_code == 200
    body = response.json()
    assert body["surge"] == 1.8
    assert body["deliveryFee"] == pytest.approx(5.4)


def test_simulate_should_not_store_any_order(client):
    client.post("/orders/simulate", json=make_payload())
    assert ORDERS == {}


def test_simulate_should_return_400_when_body_is_incomplete(client):
    response = client.post("/orders/simulate", json={"items": []})
    assert response.status_code == 400


# =============== POST /orders ===============
def test_create_order_should_return_201_with_an_id(client):
    response = client.post("/orders", json=make_payload())
    assert response.status_code == 201
    assert response.json()["id"]
    assert response.json()["total"] == 28.0


def test_create_order_should_be_retrievable_with_get(client):
    created = client.post("/orders", json=make_payload()).json()
    fetched = client.get(f"/orders/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == created


def test_create_order_should_give_distinct_ids_to_two_orders(client):
    first = client.post("/orders", json=make_payload()).json()
    second = client.post("/orders", json=make_payload()).json()
    assert first["id"] != second["id"]


def test_create_order_should_return_400_when_order_is_invalid(client):
    response = client.post("/orders", json=make_payload(items=[]))
    assert response.status_code == 400


def test_create_order_should_not_store_an_invalid_order(client):
    client.post("/orders", json=make_payload(distance=15))
    assert ORDERS == {}


# =============== GET /orders/{id} ===============
def test_get_order_should_return_200_for_existing_id(client):
    created = client.post("/orders", json=make_payload()).json()
    assert client.get(f"/orders/{created['id']}").status_code == 200


def test_get_order_should_return_404_for_unknown_id(client):
    assert client.get("/orders/does-not-exist").status_code == 404


def test_get_order_should_return_expected_structure(client):
    created = client.post("/orders", json=make_payload()).json()
    body = client.get(f"/orders/{created['id']}").json()
    assert set(body) == {"id", "items", "subtotal", "discount", "deliveryFee", "surge", "total"}


# =============== POST /promo/validate ===============
def test_promo_validate_should_return_200_and_discount_details(client):
    response = client.post("/promo/validate", json={"code": "BIENVENUE20", "amount": 50})
    assert response.status_code == 200
    assert response.json() == {
        "valid": True,
        "code": "BIENVENUE20",
        "originalAmount": 50.0,
        "discount": 10.0,
        "newTotal": 40.0,
    }


def test_promo_validate_should_return_400_with_reason_when_expired(client):
    response = client.post("/promo/validate", json={"code": "VIEUX10", "amount": 50})
    assert response.status_code == 400
    assert "expir" in response.json()["detail"].lower()


def test_promo_validate_should_return_400_when_below_minimum_order(client):
    response = client.post("/promo/validate", json={"code": "MOINS5", "amount": 10})
    assert response.status_code == 400
    assert "minimum" in response.json()["detail"].lower()


def test_promo_validate_should_return_404_when_code_is_unknown(client):
    response = client.post("/promo/validate", json={"code": "NOPE", "amount": 50})
    assert response.status_code == 404


def test_promo_validate_should_return_400_when_code_is_missing(client):
    response = client.post("/promo/validate", json={"amount": 50})
    assert response.status_code == 400


def test_promo_validate_should_not_modify_anything(client):
    client.post("/promo/validate", json={"code": "BIENVENUE20", "amount": 50})
    assert ORDERS == {}
