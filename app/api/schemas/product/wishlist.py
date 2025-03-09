from dataclasses import field
from typing import Optional, List
from pydantic import BaseModel


class WishlistCreateSchema(BaseModel):
    user_id: int
    product_id: int


class WishlistUpdateSchema(BaseModel):
    user_id: Optional[int] = None
    product_id: Optional[int] = None

    class Config:
        from_attributes = True


class WishlistResponseSchema(BaseModel):
    product_id: Optional[List[int]] = []

    class Config:
        from_attributes = True
