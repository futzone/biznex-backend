from typing import List, Optional, TypeVar
from pydantic import BaseModel, Field

from app.api.schemas.product.color import ColorResponseSchema
from app.api.schemas.product.size import SizeResponseSchema, SizeLanguageResponseSchema


class ProductCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    product_information_id: int
    warehouse_id: int
    subcategory_id: int


class ProductUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    product_information_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    subcategory_id: Optional[int] = None

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    total_come_in_price: float
    total_current_price: float
    is_sale: bool


class ProductListResponse(BaseModel):
    all_orders: int
    completed_orders: int
    canceled_orders: int
    in_process_orders: int
    total_product_variants: int
    total_sales: float
    total_come_in_price: float
    total_current_price: float
    total_profit: float
    card_orders_sum: float
    cash_orders_sum: float
    debt_orders_sum: float

    class Config:
        from_attributes = True


class WarehouseStatsResponse(BaseModel):
    warehouse_id: int
    stats: dict


class ColorSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class SizeSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MeasureSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ProductImageSchema(BaseModel):
    id: int
    image_url: str

    class Config:
        from_attributes = True


class ProductVariantSchema(BaseModel):
    id: int
    barcode: int
    come_in_price: float
    current_price: float
    old_price: Optional[float] = None
    discount: Optional[float] = None
    is_main: bool
    amount: float
    color: Optional[ColorResponseSchema] = None
    size: Optional[SizeResponseSchema | SizeLanguageResponseSchema] = None
    measure: str
    images: List[str]

    class Config:
        from_attributes = True


class WarehouseSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class SubcategorySchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ProductInformationSchema(BaseModel):
    id: int

    # ProductInformation modelidagi kerakli fieldlar

    class Config:
        from_attributes = True


class ProductResponseSchema(BaseModel):
    id: int
    rating: Optional[float] = None
    current_price: Optional[float] = 0
    old_price: Optional[float] = 0
    main_image: Optional[str] = None
    name: str
    description: Optional[str] = None
    product_information_id: int
    warehouse_id: int
    subcategory_name: str
    subcategory_id: int
    total_stock: int
    color_code: list[str]
    size: list[str]

    class Config:
        from_attributes = True


class MainProductResponseSchema(ProductResponseSchema):
    product_information: dict
    warehouse: str
    subcategory: str
    variants: List[ProductVariantSchema]

    class Config:
        from_attributes = True


class ProductLanguageResponseSchema(ProductResponseSchema):
    name: dict[str, str]
    description: Optional[dict[str, str]] = None

    class Config:
        from_attributes = True


class MainProductLanguageResponseSchema(MainProductResponseSchema):
    name: dict[str, str]
    description: Optional[dict[str, str]] = None
    subcategory: dict[str, str]

    class Config:
        from_attributes = True


class ProductFilterSchema(BaseModel):
    query: Optional[str] = Field(None, min_length=2)
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    color_id: Optional[List[int]] = Field(None, example=[5, 8])
    size_id: Optional[List[int]] = Field(None, example=[10, 12])
    measure_id: Optional[int] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    has_discount: Optional[bool] = None
    min_discount: Optional[float] = Field(None, ge=0, le=100)
    max_discount: Optional[float] = Field(None, ge=0, le=100)
    in_stock: Optional[bool] = None
    sort_by: str = Field(
        default='created_at',
        pattern=r'^(created_at|price|discount)$'
    )
    sort_order: str = Field(
        default='desc',
        pattern=r'^(asc|desc)$'
    )


T = TypeVar('T')


class ProductListResponse(BaseModel):
    products: List[T]
    total: int
    limit: int
    offset: int


class ProductVariantSalesResponse(BaseModel):
    variant_id: int
    barcode: str
    product_id: int
    product_name: str
    color: str = ""
    size: str = ""
    measure: str
    total_quantity_sold: float
    total_amount_sold: float
    order_count: int
