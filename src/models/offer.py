from typing import Literal, Optional

from pydantic import BaseModel


class Offer(BaseModel):
    offer_id: str
    round: int
    from_party: Literal["buyer", "seller"]
    material: str
    quantity: float
    unit: str
    unit_price: float
    currency: str = "EUR"
    total_price: float
    delivery_days: int
    incoterm: str
    payment_terms: str
    quality_grade: str
    carbon_per_unit_kg: Optional[float] = None
    notes: str = ""

    def summary(self) -> str:
        return (
            f"[Round {self.round}] {self.from_party.upper()} Offer #{self.offer_id}\n"
            f"  {self.material} ({self.quality_grade}) | {self.quantity} {self.unit}\n"
            f"  {self.unit_price:.2f} {self.currency}/{self.unit} | Total: {self.total_price:,.2f} {self.currency}\n"
            f"  Delivery: {self.delivery_days} days ({self.incoterm}) | {self.payment_terms}"
        )


class NegotiationMessage(BaseModel):
    round: int
    from_party: str
    message_type: Literal["rfq", "offer", "counter", "accept", "reject", "legal_review", "finalized"]
    content: str
    offer: Optional[Offer] = None
