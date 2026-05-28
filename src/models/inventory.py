from typing import Optional

from pydantic import BaseModel


class VolumeDiscount(BaseModel):
    min_quantity: float
    discount_pct: float


class InventoryItem(BaseModel):
    name: str
    unit: str
    current_stock: float
    minimum_stock: float
    monthly_consumption: float
    reorder_point: float
    lead_time_days: int
    quality_grade: str
    last_purchase_price: float
    currency: str = "EUR"

    @property
    def daily_consumption(self) -> float:
        return self.monthly_consumption / 30

    @property
    def days_until_shortage(self) -> float:
        if self.daily_consumption <= 0:
            return float("inf")
        return (self.current_stock - self.minimum_stock) / self.daily_consumption

    @property
    def needs_reorder(self) -> bool:
        return self.current_stock <= self.reorder_point


class BuyerInventory(BaseModel):
    company: str
    location: str
    last_updated: str
    materials: list[InventoryItem]

    def get_material(self, name: str) -> Optional[InventoryItem]:
        return next((m for m in self.materials if m.name == name), None)

    def get_critical_materials(self) -> list[InventoryItem]:
        return [m for m in self.materials if m.needs_reorder]


class SellerMaterial(BaseModel):
    material: str
    grade: str
    monthly_capacity: float
    unit: str
    available_next_month: float
    base_cost_per_unit: float
    currency: str = "EUR"
    carbon_per_unit_kg: float
    minimum_order: float
    volume_discounts: list[VolumeDiscount] = []

    def get_applicable_discount(self, quantity: float) -> float:
        discount = 0.0
        for vd in sorted(self.volume_discounts, key=lambda x: x.min_quantity, reverse=True):
            if quantity >= vd.min_quantity:
                discount = vd.discount_pct
                break
        return discount

    def calculate_price(self, quantity: float, margin_pct: float) -> float:
        discount = self.get_applicable_discount(quantity)
        discounted_cost = self.base_cost_per_unit * (1 - discount / 100)
        return round(discounted_cost * (1 + margin_pct / 100), 2)

    def min_profitable_price(self, quantity: float, min_margin_pct: float = 20.0) -> float:
        return self.calculate_price(quantity, min_margin_pct)


class SellerCapacity(BaseModel):
    company: str
    location: str
    certifications: list[str]
    production: list[SellerMaterial]

    def get_material(self, name: str) -> Optional[SellerMaterial]:
        return next((m for m in self.production if m.material == name), None)

    def can_fulfill(self, material: str, quantity: float) -> bool:
        mat = self.get_material(material)
        if not mat:
            return False
        return mat.available_next_month >= quantity and quantity >= mat.minimum_order
