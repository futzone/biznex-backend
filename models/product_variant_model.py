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

    def to_map(self):
        return {
            "id": self.id,
            "barcode": self.barcode,
            "product_id": self.product_id,
            "come_in_price": self.come_in_price,
            "current_price": self.current_price,
            "old_price": self.old_price,
            "discount": self.discount,
            "is_main": self.is_main,
            "amount": self.amount,
            "weight": self.weight,
            "color_id": self.color_id,
            "size_id": self.size_id,
            "measure_id": self.measure_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

