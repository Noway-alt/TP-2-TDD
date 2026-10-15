# Dates d'expiration très lointaines pour que les tests d'intégration restent stables.
PROMO_CODES = [
    {
        "code": "BIENVENUE20",
        "type": "percentage",
        "value": 20,
        "minOrder": 15.0,
        "expiresAt": "2099-12-31",
    },
    {"code": "MOINS5", "type": "fixed", "value": 5, "minOrder": 20.0, "expiresAt": "2099-12-31"},
    {
        "code": "VIEUX10",
        "type": "percentage",
        "value": 10,
        "minOrder": 0,
        "expiresAt": "2020-01-01",
    },
]
