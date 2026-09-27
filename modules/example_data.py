"""Fictional example merchant for demos.

Harvest Lane Kitchen is made up. It's shaped like a mid-size fast-casual chain on
Olo + Punchh, the most interesting combination in the fit scoring
(coexistence vs. replacement plus bidirectional loyalty sync). Numbers are
internally consistent: 2.4M annual digital orders = 200k/month.
"""

from modules.growth_model import Driver, Lever

EXAMPLE_MERCHANT = {
    "name": "Harvest Lane Kitchen",
    "pos_setup": "Olo",
    "loyalty": "Punchh",
    "annual_digital_orders": 2_400_000,
    "locations": 85,
}

EXAMPLE_BASELINE = {
    "monthly_orders": 200_000,
    "aov": 31.50,
    "conversion_pct": 8.0,
}

EXAMPLE_LEVERS = [
    Lever("Loyalty promo", Driver.TRAFFIC, lift_pct=6.0, effort=2),
    Lever("Checkout flow optimization", Driver.CONVERSION, lift_pct=5.0, effort=3),
    Lever("Paid marketing spend", Driver.TRAFFIC, lift_pct=7.0, effort=2),
    Lever("Menu/UX redesign", Driver.AOV, lift_pct=4.0, effort=4),
]

EXAMPLE_BLURB = (
    "**Harvest Lane Kitchen** (fictional): 85-location fast-casual chain on Olo "
    "(Ordering + Rails) with Punchh loyalty, ~2.4M digital orders a year."
)
