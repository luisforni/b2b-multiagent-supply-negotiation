import json
from pathlib import Path

from langchain_core.tools import tool

from src.models.inventory import BuyerInventory

_DATA = Path(__file__).parent.parent.parent / "data"


def _inventory() -> BuyerInventory:
    with open(_DATA / "buyer_inventory.json", encoding="utf-8") as f:
        return BuyerInventory(**json.load(f))


@tool
def check_inventory(material: str) -> str:
    """Return current stock, reorder status, and last purchase price for a material."""
    inv = _inventory()
    item = inv.get_material(material)
    if not item:
        available = [m.name for m in inv.materials]
        return json.dumps({"error": f"Material '{material}' not found.", "available": available})

    return json.dumps(
        {
            "material": item.name,
            "quality_grade": item.quality_grade,
            "current_stock": item.current_stock,
            "unit": item.unit,
            "minimum_stock": item.minimum_stock,
            "reorder_point": item.reorder_point,
            "needs_reorder": item.needs_reorder,
            "days_until_shortage": round(item.days_until_shortage, 1),
            "last_purchase_price": item.last_purchase_price,
            "currency": item.currency,
        }
    )


@tool
def predict_shortage(material: str, horizon_days: int = 30) -> str:
    """Forecast stock level in N days and recommend order quantity if shortage is expected."""
    inv = _inventory()
    item = inv.get_material(material)
    if not item:
        return json.dumps({"error": f"Material '{material}' not found."})

    projected = item.current_stock - item.daily_consumption * horizon_days
    shortage = projected < item.minimum_stock

    result: dict = {
        "material": item.name,
        "horizon_days": horizon_days,
        "current_stock": item.current_stock,
        "projected_stock": round(projected, 2),
        "shortage_expected": shortage,
        "days_until_shortage": round(item.days_until_shortage, 1),
    }
    if shortage:
        result["recommended_order_quantity"] = round(
            (item.minimum_stock - projected) + item.monthly_consumption * 1.5, 2
        )
    return json.dumps(result)


@tool
def get_reference_price(material: str) -> str:
    """Return the last known purchase price for a material as a negotiation reference."""
    inv = _inventory()
    item = inv.get_material(material)
    if not item:
        return json.dumps({"error": f"Material '{material}' not found."})

    return json.dumps(
        {
            "material": item.name,
            "last_purchase_price": item.last_purchase_price,
            "target_price": round(item.last_purchase_price * 0.97, 2),
            "max_acceptable_price": round(item.last_purchase_price * 1.05, 2),
            "currency": item.currency,
            "unit": item.unit,
            "quality_grade": item.quality_grade,
        }
    )


@tool
def evaluate_seller_offer(offer_json: str) -> str:
    """
    Score a seller offer (0-100) against internal benchmarks.
    offer_json must be a JSON string with keys: material, unit_price, delivery_days, payment_terms.
    """
    try:
        offer = json.loads(offer_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON. Provide: {material, unit_price, delivery_days, payment_terms}"})

    inv = _inventory()
    material = offer.get("material", "")
    item = inv.get_material(material)
    if not item:
        return json.dumps({"error": f"Unknown material: {material}"})

    unit_price = float(offer.get("unit_price", 0))
    ref = item.last_purchase_price
    price_ratio = unit_price / ref if ref > 0 else 1.0
    price_score = max(0.0, min(100.0, 200.0 - price_ratio * 100.0))

    delivery_days = int(offer.get("delivery_days", 30))
    delivery_score = max(0.0, 100.0 - max(0, delivery_days - item.lead_time_days) * 5.0)

    overall = round(price_score * 0.7 + delivery_score * 0.3, 1)

    recommendation = "accept" if overall >= 72 else "counter" if overall >= 45 else "reject"

    return json.dumps(
        {
            "material": material,
            "offered_price": unit_price,
            "reference_price": ref,
            "price_vs_reference_pct": round((unit_price / ref - 1) * 100, 1),
            "price_score": round(price_score, 1),
            "delivery_score": round(delivery_score, 1),
            "overall_score": overall,
            "recommendation": recommendation,
            "target_price": round(ref * 0.97, 2),
            "max_acceptable_price": round(ref * 1.05, 2),
        }
    )


BUYER_TOOLS = [check_inventory, predict_shortage, get_reference_price, evaluate_seller_offer]
