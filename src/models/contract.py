from typing import Literal

from pydantic import BaseModel


class ContractParty(BaseModel):
    name: str
    role: Literal["buyer", "seller"]
    location: str


class ContractLine(BaseModel):
    material: str
    quality_grade: str
    quantity: float
    unit: str
    unit_price: float
    currency: str
    carbon_per_unit_kg: float
    subtotal: float


class ContractTerms(BaseModel):
    payment_terms: str
    incoterm: str
    delivery_days: int
    governing_law: str = "Spanish Law / German Law (mutually agreed)"
    dispute_resolution: str = "ICC International Arbitration"
    force_majeure: bool = True
    applicable_tariffs: list[str] = []


class Contract(BaseModel):
    contract_id: str
    status: Literal["draft", "under_review", "approved", "rejected", "finalized"] = "draft"
    buyer: ContractParty
    seller: ContractParty
    lines: list[ContractLine]
    terms: ContractTerms
    total_value: float
    currency: str = "EUR"
    valid_from: str
    valid_until: str
    compliance_flags: list[str] = []
    legal_issues: list[str] = []

    def summary(self) -> str:
        issue_str = f"{len(self.legal_issues)} issue(s)" if self.legal_issues else "no issues"
        return (
            f"CONTRACT {self.contract_id} [{self.status.upper()}]\n"
            f"  {self.buyer.name} ← buys from → {self.seller.name}\n"
            f"  {len(self.lines)} line(s) | Total: {self.total_value:,.2f} {self.currency}\n"
            f"  Valid: {self.valid_from} → {self.valid_until}\n"
            f"  Legal: {issue_str}"
        )
