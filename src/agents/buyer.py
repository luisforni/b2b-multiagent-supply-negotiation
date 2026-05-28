import json

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from src.providers.llm import create_llm
from src.tools.buyer_tools import BUYER_TOOLS
from src.utils import extract_json, new_offer_id

_SYSTEM = """\
You are the Procurement AI Agent for {buyer_company}.

Mission: Secure raw materials at the best price while ensuring supply continuity.

Objectives (in priority order):
1. Keep unit price within 5% above last purchase price (target: 3% below)
2. Ensure delivery within lead-time requirements
3. Maintain required quality grade
4. Prefer low carbon-footprint suppliers

Negotiation rules:
- Use your tools to verify inventory levels and score the offer before deciding
- ACCEPT if overall_score >= 72 OR price is within 3% of last purchase price
- COUNTER with a specific lower price if score is 45-71
- REJECT only if score < 45 or the offer is clearly unreasonable
- Be pragmatic: accepting a slightly above-target offer is better than failing supply chain

After using your tools, output ONLY a valid JSON object (no markdown fences):
{{
  "decision": "accept" | "counter" | "reject",
  "reasoning": "<1-2 sentences>",
  "counter_offer": {{           <- include only if decision == "counter"
    "unit_price": <float>,
    "delivery_days": <int>,
    "payment_terms": "<string>",
    "notes": "<string>"
  }}
}}
"""

_SYSTEM_NO_OFFER = """\
You are the Procurement AI Agent for {buyer_company}.

Mission: Assess inventory and determine the optimal purchase request for the upcoming negotiation.

Use your tools to:
1. Check current inventory for the material
2. Predict shortage risk
3. Get reference pricing

Then output ONLY a valid JSON object:
{{
  "rfq_summary": "<brief description of why we need this material urgently>",
  "target_price": <float>,
  "max_acceptable_price": <float>,
  "urgency": "critical" | "high" | "normal"
}}
"""


def buyer_node(state: dict) -> dict:
    material = state["material"]
    quantity = state["quantity"]
    unit = state["unit"]
    current_offer = state.get("current_offer")
    round_num = state.get("round", 0)
    buyer_company = state.get("buyer_company", "AcmeCorp")

    llm = create_llm(temperature=0.1)
    agent = create_react_agent(llm, BUYER_TOOLS)

    if current_offer is None:
        system_prompt = _SYSTEM_NO_OFFER.format(buyer_company=buyer_company)
        human_text = (
            f"Material: {material}\n"
            f"Quantity needed: {quantity} {unit}\n"
            f"Analyze inventory and prepare the purchase request context."
        )
    else:
        system_prompt = _SYSTEM.format(buyer_company=buyer_company)
        human_text = (
            f"Evaluate the following seller offer (Round {round_num}):\n"
            f"Material: {material}, Quantity: {quantity} {unit}\n"
            f"Seller offer:\n{json.dumps(current_offer, indent=2)}\n\n"
            f"Use your tools to score this offer then output your decision as JSON."
        )

    result = agent.invoke(
        {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_text),
            ]
        }
    )

    last_content = result["messages"][-1].content
    data = extract_json(last_content)

    new_messages = [
        {
            "round": round_num,
            "from_party": "buyer",
            "content": last_content,
        }
    ]

    if current_offer is None:
        return {
            "buyer_target_price": data.get("target_price", state.get("buyer_target_price", 0)),
            "messages": new_messages,
        }

    decision = data.get("decision", "counter")

    if decision == "accept":
        return {
            "round": round_num + 1,
            "status": "agreed",
            "last_decision": "accept",
            "last_decision_reason": data.get("reasoning", ""),
            "messages": new_messages,
        }

    if decision == "reject":
        return {
            "round": round_num + 1,
            "status": "failed",
            "last_decision": "reject",
            "last_decision_reason": data.get("reasoning", ""),
            "messages": new_messages,
        }

    # Counter offer
    co = data.get("counter_offer", {})
    # Resolve unit_price once so both fields are consistent
    unit_price = float(co.get("unit_price") or state.get("buyer_target_price") or 0)
    counter = {
        "offer_id": new_offer_id(),
        "round": round_num + 1,
        "from_party": "buyer",
        "material": material,
        "quantity": quantity,
        "unit": unit,
        "unit_price": unit_price,
        "currency": current_offer.get("currency", "EUR"),
        "total_price": round(unit_price * quantity, 2),
        "delivery_days": co.get("delivery_days", current_offer.get("delivery_days", 21)),
        "incoterm": current_offer.get("incoterm", "DAP"),
        "payment_terms": co.get("payment_terms", "NET_30"),
        "quality_grade": current_offer.get("quality_grade", ""),
        "carbon_per_unit_kg": current_offer.get("carbon_per_unit_kg"),
        "notes": co.get("notes", ""),
    }

    return {
        "round": round_num + 1,
        "current_offer": counter,
        "offer_history": [counter],
        "last_decision": "counter",
        "last_decision_reason": data.get("reasoning", ""),
        "messages": new_messages,
    }
