from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AdminOrderItemModel(BaseModel):
    id: Optional[int] = None
    order_id: int
    product_variant_id: int
    quantity: float
    price_per_unit: float
    total_amount: float
    total_amount_with_discount: Optional[float] = None
    price_with_discount: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    notes: Optional[str] = None
