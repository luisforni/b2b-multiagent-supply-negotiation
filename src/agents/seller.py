import json

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from src.providers.llm import create_llm
from src.tools.seller_tools import SELLER_TOOLS
from src.utils import extract_json, new_offer_id

_VALID_INCOTERMS = {"EXW", "FCA", "CPT", "CIP", "DAP", "DPU", "DDP", "FAS", "FOB", "CFR", "CIF"}


def _validated_incoterm(raw: object, default: str = "DAP") -> str:
    """Normalize and validate an incoterm; fall back to default if invalid."""
    cleaned = str(raw or "").strip().upper()[:10]
    return cleaned if cleaned in _VALID_INCOTERMS else default

_SYSTEM = """\
You are the Sales AI Agent for {seller_company}.

Mission: Maximize revenue while maintaining profitable, long-term customer relationships.

Objectives (in priority order):
1. Never go below 20% profit margin on any deal
2. Target 25% margin on initial offer
3. Accept buyer counters that maintain ≥ 20% margin
4. Counter with minimum 22% margin price when needed

Negotiation rules:
- Always use your tools to verify capacity and calculate exact prices
- If the buyer counters with a price that gives you ≥ 20% margin: ACCEPT
- If the buyer counters with a price below 20% margin: COUNTER at 22% margin
- Never fabricate prices — use calculate_offer_price or evaluate_buyer_counter tools

After using your tools, output ONLY a valid JSON object (no markdown fences):
{{
  "decision": "offer" | "accept" | "counter",
  "reasoning": "<1-2 sentences>",
  "offer": {{
    "unit_price": <float>,
    "delivery_days": <int>,
    "payment_terms": "<NET_30 | NET_45 | NET_60>",
    "incoterm": "<DAP | FCA | CIP | ...>",
    "notes": "<string>"
  }}
}}
"""


def seller_node(state: dict) -> dict:
    material = state["material"]
    quantity = state["quantity"]
    unit = state["unit"]
    current_offer = state.get("current_offer")
    round_num = state.get("round", 0)
    seller_company = state.get("seller_company", "GlobalSupplyCo")

    llm = create_llm(temperature=0.1)
    agent = create_react_agent(llm, SELLER_TOOLS)

    if current_offer is None or current_offer.get("from_party") == "seller":
        # Initial offer
        human_text = (
            f"Generate your initial offer for:\n"
            f"Material: {material}, Quantity: {quantity} {unit}\n"
            f"Check production capacity and calculate price at 25% margin.\n"
            f"Use incoterm DAP, payment NET_45.\n"
            f"Output your offer as JSON."
        )
    else:
        # Responding to buyer's counter
        buyer_price = current_offer.get("unit_price", 0)
        human_text = (
            f"The buyer has countered (Round {round_num}):\n"
            f"Material: {material}, Quantity: {quantity} {unit}\n"
            f"Buyer counter price: {buyer_price} EUR/{unit}\n\n"
            f"Use evaluate_buyer_counter to check if this price gives ≥ 20% margin.\n"
            f"If acceptable: decision='accept'. Otherwise: decision='counter' with 22% margin price.\n"
            f"Output as JSON."
        )

    result = agent.invoke(
        {
            "messages": [
                SystemMessage(content=_SYSTEM.format(seller_company=seller_company)),
                HumanMessage(content=human_text),
            ]
        }
    )

    last_content = result["messages"][-1].content
    data = extract_json(last_content)

    new_messages = [{"round": round_num, "from_party": "seller", "content": last_content}]

    decision = data.get("decision", "offer")

    if decision == "accept":
        return {
            "round": round_num + 1,
            "status": "agreed",
            "last_decision": "seller_accept",
            "last_decision_reason": data.get("reasoning", ""),
            "messages": new_messages,
        }

    offer_data = data.get("offer", {})
    unit_price = float(offer_data.get("unit_price", 0))
    delivery_days = int(offer_data.get("delivery_days", 14))

    # Fallback to capacity data if LLM didn't return a price
    if unit_price <= 0:
        import json as _json
        from pathlib import Path

        cap_path = Path(__file__).parent.parent.parent / "data" / "seller_capacity.json"
        from src.models.inventory import SellerCapacity

        with open(cap_path) as f:
            cap = SellerCapacity(**_json.load(f))
        mat = cap.get_material(material)
        if mat:
            unit_price = mat.calculate_price(quantity, 25.0)

    new_offer = {
        "offer_id": new_offer_id(),
        "round": round_num + 1,
        "from_party": "seller",
        "material": material,
        "quantity": quantity,
        "unit": unit,
        "unit_price": unit_price,
        "currency": "EUR",
        "total_price": round(unit_price * quantity, 2),
        "delivery_days": delivery_days,
        "incoterm": _validated_incoterm(offer_data.get("incoterm")),
        "payment_terms": offer_data.get("payment_terms", "NET_45"),
        "quality_grade": offer_data.get("quality_grade", ""),
        "carbon_per_unit_kg": offer_data.get("carbon_per_unit_kg"),
        "notes": offer_data.get("notes", ""),
    }

    # Populate quality_grade from capacity data if missing
    if not new_offer["quality_grade"] or new_offer["carbon_per_unit_kg"] is None:
        try:
            import json as _json
            from pathlib import Path

            cap_path = Path(__file__).parent.parent.parent / "data" / "seller_capacity.json"
            from src.models.inventory import SellerCapacity

            with open(cap_path) as f:
                cap = SellerCapacity(**_json.load(f))
            mat = cap.get_material(material)
            if mat:
                if not new_offer["quality_grade"]:
                    new_offer["quality_grade"] = mat.grade
                if new_offer["carbon_per_unit_kg"] is None:
                    new_offer["carbon_per_unit_kg"] = mat.carbon_per_unit_kg
        except Exception:
            pass

    return {
        "round": round_num + 1,
        "current_offer": new_offer,
        "offer_history": [new_offer],
        "messages": new_messages,
    }
