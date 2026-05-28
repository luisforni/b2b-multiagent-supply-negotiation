#!/usr/bin/env python3
"""
B2B Multi-Agent Supply Negotiation System
==========================================
Entry point: detects inventory shortages and runs an autonomous
LLM-powered negotiation between Buyer, Seller, and Legal agents.
"""
import json
import uuid
from pathlib import Path

from config import get_settings
from src.models.inventory import BuyerInventory
from src.orchestrator.graph import build_negotiation_graph
from src.orchestrator.state import NegotiationState


def _load_inventory() -> BuyerInventory:
    path = Path(__file__).parent / "data" / "buyer_inventory.json"
    with open(path, encoding="utf-8") as f:
        return BuyerInventory(**json.load(f))


def _select_material(inventory: BuyerInventory) -> tuple[str, float, str]:
    critical = inventory.get_critical_materials()
    mat = min(critical, key=lambda m: m.days_until_shortage) if critical else inventory.materials[0]
    quantity = round(mat.monthly_consumption * 3, 0)
    return mat.name, quantity, mat.unit


def _divider(char: str = "=", width: int = 60) -> str:
    return char * width


def main() -> None:
    settings = get_settings()
    inventory = _load_inventory()
    material, quantity, unit = _select_material(inventory)
    mat_item = inventory.get_material(material)

    print(f"\n{_divider()}")
    print("  B2B MULTI-AGENT SUPPLY NEGOTIATION SYSTEM")
    print(_divider())
    print(f"  Provider  : {settings.provider.upper()}")
    print(f"  Buyer     : {settings.buyer_company}")
    print(f"  Seller    : {settings.seller_company}")
    print(_divider())
    print(f"\n[ALERT] Inventory shortage detected:")
    print(f"  Material       : {material}")
    print(f"  Current stock  : {mat_item.current_stock} {unit}")
    print(f"  Reorder point  : {mat_item.reorder_point} {unit}")
    print(f"  Days remaining : {mat_item.days_until_shortage:.1f}")
    print(f"  Order quantity : {quantity} {unit}")
    print(f"\n[START] Launching autonomous negotiation...\n{_divider('-')}")

    initial_state: NegotiationState = {
        "session_id": str(uuid.uuid4())[:8].upper(),
        "material": material,
        "quantity": quantity,
        "unit": unit,
        "round": 0,
        "max_rounds": settings.max_rounds,
        "status": "negotiating",
        "buyer_company": settings.buyer_company,
        "seller_company": settings.seller_company,
        "buyer_target_price": round(mat_item.last_purchase_price * 0.97, 2),
        "seller_min_margin_pct": 20.0,
        "current_offer": None,
        "offer_history": [],
        "messages": [],
        "contract_draft": None,
        "legal_issues": [],
        "last_decision": None,
        "last_decision_reason": None,
        "final_decision": None,
    }

    graph = build_negotiation_graph()

    try:
        final = graph.invoke(initial_state)
    except KeyboardInterrupt:
        print("\n[STOP] Interrupted by user.")
        return

    print(f"\n{_divider()}")
    print("  NEGOTIATION RESULT")
    print(_divider())
    status = final.get("status", "unknown").upper()
    rounds = final.get("round", 0)
    print(f"  Status  : {status}")
    print(f"  Rounds  : {rounds}")

    contract = final.get("contract_draft")
    if contract and final.get("status") in ("finalized", "under_review", "agreed"):
        print(f"  Contract: {contract.get('contract_id', 'N/A')}")
        print(f"  Value   : {contract.get('total_value', 0):,.2f} {contract.get('currency', 'EUR')}")
        print(f"  Verdict : {contract.get('legal_verdict', 'N/A')}")
        if contract.get("legal_issues"):
            print("  Issues  :")
            for issue in contract["legal_issues"]:
                print(f"    - {issue}")
        if contract.get("compliance_flags"):
            print("  Warnings:")
            for w in contract["compliance_flags"]:
                print(f"    ~ {w}")
    elif final.get("status") == "failed":
        print("  Outcome : Negotiation failed — escalate to human negotiator.")

    print(_divider())

    # Dump full offer history for audit trail
    history = final.get("offer_history", [])
    if history:
        print(f"\n  Offer history ({len(history)} offers):")
        for o in history:
            print(
                f"    [{o.get('from_party', '?').upper():6s}] Round {o.get('round', '?'):>2} "
                f"| {o.get('unit_price', 0):>8.2f} EUR/{unit} "
                f"| Total {o.get('total_price', 0):>12,.2f} EUR"
            )
    print()


if __name__ == "__main__":
    main()
