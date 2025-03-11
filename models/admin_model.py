from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OrderBaseModel(BaseModel):
    id: Optional[int] = None
    by: Optional[int] = None
    seller: Optional[int] = None
    status: Optional[str] = None
    updated_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    total_amount_with_discount: Optional[float] = None
    total_amount: Optional[float] = None
    warehouse_id: Optional[int] = None
    payment_type: Optional[str] = None
    created_at: Optional[datetime] = None
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    notes: Optional[str] = None
