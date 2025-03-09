from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class PromotionBase(BaseModel):
    name: str
    discount: float
    product_limit: int
    warehouse_id: int
    is_active: bool = True

class PromotionCreate(PromotionBase):
    product_variant_ids: List[int]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PromotionUpdate(PromotionBase):
    product_variant_ids: Optional[List[int]]

class PromotionResponse(PromotionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes=True