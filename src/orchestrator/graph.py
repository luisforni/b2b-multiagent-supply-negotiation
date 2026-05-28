from langgraph.graph import END, StateGraph

from src.agents.buyer import buyer_node
from src.agents.legal import legal_node
from src.agents.seller import seller_node
from src.orchestrator.state import NegotiationState


def _route_after_seller(state: NegotiationState) -> str:
    status = state.get("status", "negotiating")
    if status == "agreed":
        return "legal"
    if status == "failed":
        return END
    if state.get("round", 0) >= state.get("max_rounds", 10):
        return END
    return "buyer"


def _route_after_buyer(state: NegotiationState) -> str:
    status = state.get("status", "negotiating")
    if status == "agreed":
        return "legal"
    if status == "failed":
        return END
    if state.get("round", 0) >= state.get("max_rounds", 10):
        return END
    return "seller"


def _print_round_header(state: NegotiationState) -> NegotiationState:
    """Passthrough node that prints progress to stdout."""
    rnd = state.get("round", 0)
    offer = state.get("current_offer")
    status = state.get("status", "negotiating")
    print(f"\n  [Round {rnd}] status={status}", end="")
    if offer:
        price = offer.get("unit_price", "?")
        party = offer.get("from_party", "?")
        print(f"  | latest offer from {party}: {price} EUR", end="")
    print()
    return {}


def build_negotiation_graph() -> "CompiledGraph":  # type: ignore[name-defined]
    g = StateGraph(NegotiationState)

    g.add_node("seller", seller_node)
    g.add_node("buyer", buyer_node)
    g.add_node("legal", legal_node)

    # Negotiation starts with seller's initial offer
    g.set_entry_point("seller")

    g.add_conditional_edges(
        "seller",
        _route_after_seller,
        {"buyer": "buyer", "legal": "legal", END: END},
    )
    g.add_conditional_edges(
        "buyer",
        _route_after_buyer,
        {"seller": "seller", "legal": "legal", END: END},
    )
    g.add_edge("legal", END)

    return g.compile()
