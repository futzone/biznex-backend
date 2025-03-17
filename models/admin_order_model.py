from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AdminOrderModel(BaseModel):
    id: Optional[int] = None
    by: int
    seller: Optional[int]
    status: str
    updated_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    total_amount_with_discount: Optional[float] = None
    total_amount: float
    warehouse_id: int
    payment_type: str
    created_at: Optional[datetime] = None
    user_name: str
    user_phone: str
    notes: Optional[str] = None
