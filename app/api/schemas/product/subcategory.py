from typing import Optional, Dict
from pydantic import BaseModel


class SubcategoryCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: int


class SubcategoryUpdateSchema(BaseModel):
    name: Optional[str] = ""
    description: Optional[str] = ""
    category_id: int

    class Config:
        from_attributes = True


class SubcategoryResponseSchema(SubcategoryCreateSchema):
    id: int

    class Config:
        from_attributes = True


class SubcategoryCreateResponseSchema(BaseModel):
    id: int
    name: Dict[str, str] = {}
    description: Dict[str, str] = {}
    category_id: int

    class Config:
        from_attributes = True

class SubcategoryWarehouseCreateResponseSchema(BaseModel):
    id: int
    name: str
    description: str
    category_id: int
    warehouse_id: int

    class Config:
        from_attributes = True