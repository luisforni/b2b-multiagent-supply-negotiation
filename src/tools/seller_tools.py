import json
from pathlib import Path

from langchain_core.tools import tool

from src.models.inventory import SellerCapacity

_DATA = Path(__file__).parent.parent.parent / "data"


def _capacity() -> SellerCapacity:
    with open(_DATA / "seller_capacity.json", encoding="utf-8") as f:
        return SellerCapacity(**json.load(f))


@tool
def check_production_capacity(material: str, quantity: float) -> str:
    """Check if we can fulfill a given quantity of a material and return availability details."""
    cap = _capacity()
    mat = cap.get_material(material)
    if not mat:
        available = [m.material for m in cap.production]
        return json.dumps({"error": f"Material '{material}' not produced.", "available": available})

    return json.dumps(
        {
            "material": mat.material,
            "grade": mat.grade,
            "requested_quantity": quantity,
            "unit": mat.unit,
            "available_next_month": mat.available_next_month,
            "monthly_capacity": mat.monthly_capacity,
            "can_fulfill": cap.can_fulfill(material, quantity),
            "minimum_order": mat.minimum_order,
            "certifications": cap.certifications,
            "carbon_per_unit_kg": mat.carbon_per_unit_kg,
        }
    )


@tool
def calculate_min_price(material: str, quantity: float) -> str:
    """Calculate the minimum profitable price (20% margin floor) for a given material and quantity."""
    cap = _capacity()
    mat = cap.get_material(material)
    if not mat:
        return json.dumps({"error": f"Material '{material}' not produced."})

    min_price = mat.min_profitable_price(quantity, min_margin_pct=20.0)
    discount = mat.get_applicable_discount(quantity)

    return json.dumps(
        {
            "material": mat.material,
            "quantity": quantity,
            "base_cost_per_unit": mat.base_cost_per_unit,
            "volume_discount_pct": discount,
            "min_price_20pct_margin": min_price,
            "currency": mat.currency,
            "unit": mat.unit,
        }
    )


@tool
def calculate_offer_price(material: str, quantity: float, margin_pct: float = 25.0) -> str:
    """
    Calculate an offer price at the specified margin percentage.
    Default margin is 25%. Minimum profitable margin is 20%.
    Returns unit price, total price, and applicable volume discounts.
    """
    cap = _capacity()
    mat = cap.get_material(material)
    if not mat:
        return json.dumps({"error": f"Material '{material}' not produced."})

    if margin_pct < 20.0:
        margin_pct = 20.0

    unit_price = mat.calculate_price(quantity, margin_pct)
    total = round(unit_price * quantity, 2)
    discount = mat.get_applicable_discount(quantity)

    return json.dumps(
        {
            "material": mat.material,
            "quantity": quantity,
            "unit": mat.unit,
            "margin_pct": margin_pct,
            "volume_discount_applied_pct": discount,
            "unit_price": unit_price,
            "total_price": total,
            "currency": mat.currency,
            "carbon_per_unit_kg": mat.carbon_per_unit_kg,
        }
    )


@tool
def evaluate_buyer_counter(material: str, buyer_price: float, quantity: float) -> str:
    """
    Evaluate whether a buyer's counter-offer price is acceptable.
    Returns margin analysis and a recommended response price.
    """
    cap = _capacity()
    mat = cap.get_material(material)
    if not mat:
        return json.dumps({"error": f"Material '{material}' not produced."})

    discount = mat.get_applicable_discount(quantity)
    effective_cost = mat.base_cost_per_unit * (1 - discount / 100)
    implied_margin = ((buyer_price - effective_cost) / effective_cost) * 100 if effective_cost > 0 else 0

    acceptable = implied_margin >= 20.0
    min_price = mat.min_profitable_price(quantity, 20.0)
    recommended_counter = mat.calculate_price(quantity, 22.0)

    return json.dumps(
        {
            "material": mat.material,
            "buyer_offered_price": buyer_price,
            "effective_production_cost": round(effective_cost, 2),
            "implied_margin_pct": round(implied_margin, 1),
            "acceptable": acceptable,
            "min_acceptable_price": min_price,
            "recommended_counter_price": recommended_counter,
            "decision": "accept" if acceptable else "counter",
        }
    )


SELLER_TOOLS = [check_production_capacity, calculate_min_price, calculate_offer_price, evaluate_buyer_counter]
