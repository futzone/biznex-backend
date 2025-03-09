from typing import Optional, List
from pydantic import BaseModel, Field


class ProductMinimalResponse(BaseModel):
    id: int
    name: dict[str, str]

    class Config:
        from_attributes = True


class ColorResponse(BaseModel):
    id: int
    name: dict[str, str]
    hex_code: str

    class Config:
        from_attributes = True


class SizeResponse(BaseModel):
    id: int
    size: str
    description: Optional[dict[str, str]] = None

    class Config:
        from_attributes = True


class MeasureResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ProductImageResponse(BaseModel):
    id: int
    alt_text: Optional[str] = None
    image: str
    is_main: bool

    class Config:
        from_attributes = True


class ProductVariantCreateSchema(BaseModel):
    barcode: int = 0
    come_in_price: float
    current_price: float
    old_price: Optional[float] = None
    discount: Optional[float] = None
    is_main: bool = False
    amount: float
    weight: Optional[float] = None

    color_id: Optional[int] = None
    size_id: Optional[int] = None
    measure_id: int


class ProductVariantUpdateSchema(BaseModel):
    barcode: Optional[int] = None
    come_in_price: Optional[float] = None
    current_price: Optional[float] = None
    old_price: Optional[float] = None
    discount: Optional[float] = None
    is_main: Optional[bool] = None
    amount: Optional[float] = None
    weight: Optional[float] = None
    color_id: Optional[int] = None
    size_id: Optional[int] = None
    measure_id: Optional[int] = None

    class Config:
        from_attributes = True


class ProductVariantResponseSchema(BaseModel):
    id: int
    barcode: int
    product: Optional[ProductMinimalResponse]
    come_in_price: float
    current_price: float
    old_price: Optional[float] = None
    discount: Optional[float] = None
    is_main: bool
    amount: float

    color: Optional[ColorResponse] = None
    size: Optional[SizeResponse] = None
    measure: MeasureResponse

    main_image: Optional[str] = None
    images: List[ProductImageResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
