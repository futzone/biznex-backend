from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProductVariantModel(BaseModel):
    id: Optional[int] = None
    barcode: Optional[int] = None
    product_id: Optional[int]
    come_in_price: Optional[float] = 0.0
    current_price: Optional[float] = 0.0
    old_price: Optional[float] = None
    discount: Optional[float] = None
    is_main: Optional[bool] = False
    amount: Optional[float] = 0.0
    weight: Optional[float] = 0.0
    color_id: Optional[int] = None
    size_id: Optional[int] = None
    measure_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
