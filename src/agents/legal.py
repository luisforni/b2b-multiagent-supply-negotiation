import json
from datetime import date, timedelta

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from src.providers.llm import create_llm
from src.tools.legal_tools import LEGAL_TOOLS
from src.utils import contract_id, extract_json

_SYSTEM = """\
You are the Legal & Compliance AI Agent for B2B international supply contracts.

Your mandate: Review the agreed terms and verify full compliance before contract finalization.

Review checklist:
1. Validate the Incoterm (must be Incoterms® 2020 compliant)
2. Check applicable tariffs (Germany → Spain, EU internal trade)
3. Verify carbon footprint vs EU CBAM thresholds
4. Validate payment terms (EU Late Payment Directive: max 60 days B2B)
5. Confirm mandatory clauses: force majeure, dispute resolution, governing law

Risk levels:
- BLOCKER: contract cannot proceed without resolution
- WARNING: flag for human review but does not block
- OK: fully compliant

After using your tools, output ONLY a valid JSON object (no markdown fences):
{{
  "verdict": "APPROVED" | "CONDITIONALLY_APPROVED" | "REJECTED",
  "issues": [           <- BLOCKERs only
    {{"type": "BLOCKER", "description": "<issue>"}}
  ],
  "warnings": [         <- WARNINGs
    {{"type": "WARNING", "description": "<warning>"}}
  ],
  "reasoning": "<2-3 sentences summarizing the review>"
}}
"""


def legal_node(state: dict) -> dict:
    material = state["material"]
    quantity = state["quantity"]
    unit = state["unit"]
    current_offer = state.get("current_offer", {}) or {}
    buyer_company = state.get("buyer_company", "AcmeCorp")
    seller_company = state.get("seller_company", "GlobalSupplyCo")
    session_id = state.get("session_id", "UNKNOWN")

    terms_for_review = {
        "incoterm": current_offer.get("incoterm", "DAP"),
        "payment_terms": current_offer.get("payment_terms", "NET_45"),
        "force_majeure": True,
        "dispute_resolution": "ICC_Arbitration",
        "governing_law": "Spanish Law / German Law (mutually agreed)",
    }

    human_text = (
        f"Review the following agreed deal for contract compliance:\n\n"
        f"Parties: {buyer_company} (buyer, Barcelona, Spain) ↔ {seller_company} (seller, Düsseldorf, Germany)\n"
        f"Material: {material}, {quantity} {unit}\n"
        f"Unit price: {current_offer.get('unit_price', 0)} {current_offer.get('currency', 'EUR')}/{unit}\n"
        f"Total value: {current_offer.get('total_price', 0)} {current_offer.get('currency', 'EUR')}\n"
        f"Incoterm: {terms_for_review['incoterm']}\n"
        f"Payment terms: {terms_for_review['payment_terms']}\n"
        f"Carbon per unit: {current_offer.get('carbon_per_unit_kg', 'unknown')} kg CO2\n\n"
        f"Contract terms JSON:\n{json.dumps(terms_for_review)}\n\n"
        f"Run all compliance checks and output your verdict as JSON."
    )

    llm = create_llm(temperature=0.0)
    agent = create_react_agent(llm, LEGAL_TOOLS)

    result = agent.invoke(
        {
            "messages": [
                SystemMessage(content=_SYSTEM),
                HumanMessage(content=human_text),
            ]
        }
    )

    last_content = result["messages"][-1].content
    data = extract_json(last_content)

    verdict = data.get("verdict", "CONDITIONALLY_APPROVED")
    issues = [i.get("description", str(i)) for i in data.get("issues", [])]
    warnings = [w.get("description", str(w)) for w in data.get("warnings", [])]

    new_status = "finalized" if verdict == "APPROVED" else "under_review"

    valid_from = date.today().isoformat()
    valid_until = (date.today() + timedelta(days=180)).isoformat()

    unit_price = current_offer.get("unit_price", 0)
    total_price = current_offer.get("total_price") or round(unit_price * quantity, 2)

    contract = {
        "contract_id": contract_id(),
        "status": new_status,
        "session_id": session_id,
        "buyer": {"name": buyer_company, "role": "buyer", "location": "Barcelona, Spain"},
        "seller": {"name": seller_company, "role": "seller", "location": "Düsseldorf, Germany"},
        "lines": [
            {
                "material": material,
                "quality_grade": current_offer.get("quality_grade", ""),
                "quantity": quantity,
                "unit": unit,
                "unit_price": unit_price,
                "currency": current_offer.get("currency", "EUR"),
                "carbon_per_unit_kg": current_offer.get("carbon_per_unit_kg", 0),
                "subtotal": total_price,
            }
        ],
        "terms": {
            "payment_terms": terms_for_review["payment_terms"],
            "incoterm": terms_for_review["incoterm"],
            "delivery_days": current_offer.get("delivery_days", 14),
            "governing_law": terms_for_review["governing_law"],
            "dispute_resolution": terms_for_review["dispute_resolution"],
            "force_majeure": terms_for_review["force_majeure"],
            "applicable_tariffs": [],
        },
        "total_value": total_price,
        "currency": current_offer.get("currency", "EUR"),
        "valid_from": valid_from,
        "valid_until": valid_until,
        "compliance_flags": warnings,
        "legal_issues": issues,
        "legal_verdict": verdict,
        "legal_reasoning": data.get("reasoning", ""),
    }

    new_messages = [
        {
            "round": state.get("round", 0),
            "from_party": "legal",
            "content": last_content,
        }
    ]

    return {
        "status": new_status,
        "contract_draft": contract,
        "legal_issues": issues,
        "final_decision": verdict,
        "messages": new_messages,
    }
