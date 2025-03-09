from typing import List, Optional, Dict, Union
from pydantic import BaseModel, Field


class CategoryCreateSchema(BaseModel):
    name: str
    image: Optional[str] = None
    description: Optional[str] = None


class CategoryUpdateSchema(BaseModel):
    name: Optional[str]
    image: Optional[str] = None
    description: Optional[str] = Field(default_factory=str)

    class Config:
        from_attributes = True


class CategoryResponseSchema(CategoryCreateSchema):
    id: int
    name: str
    image: Optional[str] = None
    description: Optional[str] = None
    product_count: Optional[int] = None

    class Config:
        from_attributes = True


class CategoryCreateResponseSchema(BaseModel):
    id: int
    name: Dict[str, str]
    image: Optional[str] = None
    description: Optional[Dict[str, str]] = Field(default_factory=dict)

    class Config:
        from_attributes = True
        
class WarehouseCategoryCreate(BaseModel):
    warehouse_id: int
    global_category_id: int
    name: str
    description: Optional[str] = Field(default_factory=str)


class WarehouseCategoryUpdate(BaseModel):
    name: str = None
    description: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class WarehouseSubcategoryCreate(BaseModel):
    warehouse_id: int
    subcategory_id: int
    warehouse_category_id: int
    name: str
    description: Optional[str] = Field(default_factory=str)


class WarehouseSubcategoryUpdate(BaseModel):
    name: str = None
    description: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class SubcategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[Union[str, Dict[str, str]]]
    is_active: bool
    subcategory_id: int


class WarehouseCategoryResponse(BaseModel):
    id: int
    name: Union[str, Dict[str, str]]
    image: Optional[str]
    description: Optional[Union[str, Dict[str, str]]]
    global_category_id: int
    warehouse_id: int
    is_active: bool
    subcategories: Optional[List[SubcategoryResponse]] = None


class WarehouseSubcategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    product_count: int
    subcategory_id: int
    warehouse_id: int
    warehouse_category_id: int
    is_active: bool


class WarehouseCategoryListResponse(BaseModel):
    categories: List[WarehouseCategoryResponse]


class WarehouseSubcategoryListResponse(BaseModel):
    subcategories: List[WarehouseSubcategoryResponse]