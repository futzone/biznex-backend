from typing import Optional, Dict, Any
from pydantic import BaseModel


class ProductInformationBase(BaseModel):
    product_type: Optional[str] = None
    brand: str
    model_name: Optional[str] = None
    description: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ProductInformationCreateSchema(ProductInformationBase):
    warehouse_id: int
    product_type: str
    brand: Optional[str] = None
    model_name: Optional[str] = None
    description: Optional[str] = None


class ProductInformationUpdateSchema(ProductInformationBase):
    brand: Optional[str] = None
    model_name: Optional[str] = None
    description: dict[str, str] | None = None


class ProductInformationResponseSchema(ProductInformationCreateSchema):
    id: int

    class Config:
        from_attributes = True


class ProductInformationLanguageResponseSchema(ProductInformationCreateSchema):
    id: int
    description: dict[str, str] | None = None

    class Config:
        from_attributes = True
