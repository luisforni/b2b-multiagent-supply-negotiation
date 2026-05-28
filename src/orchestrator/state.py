import operator
from typing import Annotated, Optional

from typing_extensions import TypedDict


class NegotiationState(TypedDict):
    # Session metadata
    session_id: str
    material: str
    quantity: float
    unit: str
    round: int
    max_rounds: int
    status: str  # negotiating | agreed | failed | under_review | finalized

    # Parties
    buyer_company: str
    seller_company: str

    # Pricing targets
    buyer_target_price: float
    seller_min_margin_pct: float

    # Negotiation data (Annotated with operator.add = append-only lists)
    current_offer: Optional[dict]
    offer_history: Annotated[list[dict], operator.add]
    messages: Annotated[list[dict], operator.add]

    # Contract output
    contract_draft: Optional[dict]
    legal_issues: Annotated[list[str], operator.add]
    last_decision: Optional[str]
    last_decision_reason: Optional[str]
    final_decision: Optional[str]
