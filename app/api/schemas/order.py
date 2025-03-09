from decimal import Decimal

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional
from enum import Enum

from app.api.models.order import AdminOrderItem
from app.api.models.product import ProductVariant
from app.core.models.enums import AdminOrderStatusEnum


class OrderStatusEnum(str, Enum):
    pending = "pending"
    completed = "completed"
    canceled = "canceled"
    # Add other statuses as required


class OrderTypeEnum(str, Enum):
    regular = "regular"
    express = "express"
    # Add other types as required


class OrderItemBase(BaseModel):
    product_id: int
    quantity: float
    total_amount: float


class OrderItemCreate(OrderItemBase):
    pass


class OrderItem(OrderItemBase):
    id: int
    created_at: datetime
    product_id: int

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    user_id: int
    status: OrderStatusEnum
    type: OrderTypeEnum
    total_amount: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    items: List[OrderItemCreate]


class OrderCreate(OrderBase):
    pass


class Order(OrderBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class AdminOrderItemSchema(BaseModel):
    id: int
    product_variant_id: int
    quantity: float
    price_per_unit: float
    total_amount: float


class AdminOrderCreate(BaseModel):
    id: int
    by: int
    seller_id: Optional[int] = None
    status: AdminOrderStatusEnum
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    total_amount: Decimal = Decimal('0')
    total_amount_with_discount: Decimal = Decimal('0') 
    payment_type: Optional[str]
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None

    class Config:
        from_attributes = True





class OrderItemRequest(BaseModel):
    barcode: str
    quantity: int = 1
    custom_price: Optional[Decimal] = None

class CompleteOrderRequest(BaseModel):
    seller_id: Optional[int] = None
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    payment_type: str = Field(default="cash")
    status: str = Field(default="opened", pattern="^(opened|completed|canceled)$")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)

    items: List[OrderItemRequest]

class AdminOrderUpdate(BaseModel):
    status: str
    seller_id: Optional[int] = None
    notes: str | None
    user_name: str | None
    user_phone: str | None
    payment_type: Optional[str]
    with_discount: bool = Field(default=True, description="Whether to apply promotions/discounts")




class AdminProductVariantResponse(BaseModel):
    id: int
    barcode: str
    name: str
    current_price: Decimal
    color: Optional[str] = None
    size: Optional[str] = None
    measure: str
    images: list[str]

    @classmethod
    def from_variant(cls, variant: Optional['ProductVariant'], language: str) -> "AdminProductVariantResponse":
        if variant is None:
            return cls(
                id=0,
                barcode="N/A",
                name="",
                current_price=Decimal('0'),
                color=None,
                size=None,
                measure="N/A",
                images=[]
            )
            
        return cls(
            id=variant.id,
            barcode=str(variant.barcode),
            name=variant.product.name.get(language, "") if hasattr(variant, 'product') and variant.product else "",
            current_price=variant.current_price,
            color=variant.color.name.get(language) if variant.color else None,
            size=variant.size.size if variant.size else None,
            measure=variant.measure.name,
            images=[img.image for img in variant.images]
        )

class AdminOrderItemResponse(BaseModel):
    id: int
    order_id: int
    product_variant: AdminProductVariantResponse
    quantity: float
    price_per_unit: Decimal
    total_amount_with_discount: Decimal = Decimal('0') 
    price_with_discount: Decimal
    total_amount: Decimal
    payment_type: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

    @classmethod
    def from_order_item(cls, order_item: 'AdminOrderItem', language: str) -> "AdminOrderItemResponse":
        product_variant_obj = getattr(order_item, 'product_variant', None)
        
        return cls(
            id=order_item.id,
            order_id=order_item.order_id,
            product_variant=AdminProductVariantResponse.from_variant(
                product_variant_obj, 
                language
            ),
            quantity=order_item.quantity,
            price_per_unit=order_item.price_per_unit,
            total_amount=order_item.total_amount,
            price_with_discount=order_item.price_with_discount,
            total_amount_with_discount=order_item.total_amount_with_discount,
            notes=order_item.notes,
            created_at=order_item.created_at,
            updated_at=order_item.updated_at
        )


class AdminOrderItemReturnSchema(BaseModel):
    order_id: int  
    return_quantity: int = Field(..., gt=0)  # Faqat musbat sonlar qabul qilinadi

    @validator('return_quantity')
    def validate_return_quantity(cls, v):
        if v <= 0:
            raise ValueError("Return quantity must be greater than 0")
        return v



class AdminOrderResponse(AdminOrderCreate):
    payment_type: Optional[str] = None
    product_variants: List[AdminOrderItemResponse] = []

    class Config:
        from_attributes = True


class BatchOrderItemsRequest(BaseModel):
    items: List[OrderItemRequest]