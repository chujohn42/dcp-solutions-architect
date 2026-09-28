"""Fictional example merchant for demos.

Harvest Lane Kitchen is made up. It's shaped like a mid-size fast-casual chain on
Olo + Punchh, the most interesting combination in the fit scoring
(run-both-or-replace plus real-time loyalty sync).
"""

from modules.growth_model import Driver, Lever

EXAMPLE_MERCHANT = {
    "name": "Harvest Lane Kitchen",
    "pos_setup": "Olo",
    "loyalty": "Punchh",
}

EXAMPLE_BASELINE = {
    "monthly_orders": 200_000,
    "aov": 31.50,
    "conversion_pct": 8.0,
}

# Same order and names as growth_model.DEFAULT_LEVERS.
EXAMPLE_LEVERS = [
    Lever("Loyalty promo", Driver.TRAFFIC, lift_pct=6.0),
    Lever("Checkout flow optimization", Driver.CONVERSION, lift_pct=5.0),
    Lever("Paid marketing spend", Driver.TRAFFIC, lift_pct=7.0),
    Lever("Menu/UX redesign", Driver.AOV, lift_pct=4.0),
]
