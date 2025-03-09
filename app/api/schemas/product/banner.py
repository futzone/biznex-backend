from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class BannerBase(BaseModel):
    title: str
    description: Optional[str]
    image_url: str
    discount_percentage: float
    start_date: datetime
    end_date: datetime
    is_active: bool = True

class BannerCreate(BannerBase):
    product_variant_ids: List[int]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BannerUpdate(BannerBase):
    product_variant_ids: Optional[List[int]]

class BannerResponse(BannerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True