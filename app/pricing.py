"""Moteur de tarification. Fonctions pures : heure et date sont des paramètres."""

from datetime import date

BASE_FEE = 2.00
FREE_DISTANCE_KM = 3
MAX_DISTANCE_KM = 10
FEE_PER_KM = 0.50
HEAVY_WEIGHT_KG = 5
HEAVY_SURCHARGE = 1.50

OPENING_HOUR = 10
CLOSING_HOUR = 22
VALID_DAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}
FRIDAY_SATURDAY = {"friday", "saturday"}


class PricingError(ValueError):
    """Entrée invalide ou commande refusée."""


class PromoNotFoundError(PricingError):
    """Le code promo n'existe pas."""


class PromoRefusedError(PricingError):
    """Le code promo existe mais n'est pas applicable (expiré, minimum non atteint)."""


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# ---------- Fonction 1 ----------
def calculate_delivery_fee(distance, weight):
    if not _is_number(distance) or not _is_number(weight):
        raise PricingError("Distance et poids doivent être des nombres")
    if distance < 0 or weight < 0:
        raise PricingError("Distance et poids ne peuvent pas être négatifs")
    if distance > MAX_DISTANCE_KM:
        raise PricingError("Livraison refusée : hors zone (> 10 km)")

    fee = BASE_FEE + max(0, distance - FREE_DISTANCE_KM) * FEE_PER_KM
    if weight > HEAVY_WEIGHT_KG:
        fee += HEAVY_SURCHARGE
    return round(fee, 2)


# ---------- Fonction 2 ----------
def apply_promo_code(subtotal, promo_code, promo_codes, today):
    if not _is_number(subtotal) or subtotal < 0:
        raise PricingError("Le sous-total doit être un nombre positif")
    if not promo_code:
        return round(subtotal, 2)

    promo = next((p for p in promo_codes if p["code"] == promo_code), None)
    if promo is None:
        raise PromoNotFoundError(f"Code promo inconnu : {promo_code}")
    if today > date.fromisoformat(promo["expiresAt"]):
        raise PromoRefusedError("Code promo expiré")
    if subtotal < promo["minOrder"]:
        raise PromoRefusedError(f"Commande minimum de {promo['minOrder']:.2f} € non atteinte")

    if promo["type"] == "percentage":
        total = subtotal * (1 - promo["value"] / 100)
    elif promo["type"] == "fixed":
        total = subtotal - promo["value"]
    else:
        raise PricingError(f"Type de promo invalide : {promo['type']}")
    return round(max(total, 0), 2)


# ---------- Fonction 3 ----------
def calculate_surge(hour, day_of_week):
    day = day_of_week.lower() if isinstance(day_of_week, str) else None
    if day not in VALID_DAYS:
        raise PricingError(f"Jour invalide : {day_of_week}")
    if not _is_number(hour) or hour < 0 or hour >= 24:
        raise PricingError(f"Heure invalide : {hour}")

    if hour < OPENING_HOUR or hour >= CLOSING_HOUR:
        return 0
    if day == "sunday":
        return 1.2
    if day in FRIDAY_SATURDAY:
        return 1.8 if hour >= 19 else 1.0
    if 12 <= hour < 13.5:
        return 1.3
    if 19 <= hour < 21:
        return 1.5
    return 1.0


# ---------- Fonction 4 ----------
def _validate_items(items):
    if not isinstance(items, list) or not items:
        raise PricingError("Le panier est vide")
    for item in items:
        price, quantity = item.get("price"), item.get("quantity")
        if not _is_number(price) or price < 0:
            raise PricingError("Prix d'article invalide")
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
            raise PricingError("Quantité d'article invalide")


def calculate_order_total(
    items, distance, weight, promo_code, hour, day_of_week, promo_codes, today
):
    _validate_items(items)
    subtotal = round(sum(i["price"] * i["quantity"] for i in items), 2)

    surge = calculate_surge(hour, day_of_week)
    if surge == 0:
        raise PricingError("Restaurant fermé à cette heure")

    base_fee = calculate_delivery_fee(distance, weight)
    discounted = apply_promo_code(subtotal, promo_code, promo_codes, today)

    discount = round(subtotal - discounted, 2)
    delivery_fee = round(base_fee * surge, 2)  # le surge ne touche que la livraison
    total = round(discounted + delivery_fee, 2)

    return {
        "subtotal": subtotal,
        "discount": discount,
        "deliveryFee": delivery_fee,
        "surge": surge,
        "total": total,
    }
