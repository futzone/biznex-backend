from typing import Optional
from pydantic import BaseModel


class ProductImageCreateSchema(BaseModel):
    product_variant_id: int
    alt_text: Optional[str] = None
    image: str
    is_main: bool = False


class ProductImageUpdateSchema(BaseModel):
    product_variant_id: Optional[int] = None
    alt_text: Optional[str] = None
    image: Optional[str] = None
    is_main: Optional[bool] = None

    class Config:
        from_attributes = True


class ProductImageResponseSchema(ProductImageCreateSchema):
    id: int

    class Config:
        from_attributes = True


class ProductImageDelete(BaseModel):
    path: Optional[str] = None
    variant_id: Optional[int] = None
