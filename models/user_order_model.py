from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class UserOrder(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    status: Optional[str] = "pending"
    type: Optional[str] = "regular"
    total_amount: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None

    def to_map(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "type": self.type,
            "total_amount": self.total_amount,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "canceled_at": self.canceled_at.isoformat() if self.canceled_at else None
        }


class UserOrderItem(BaseModel):
    id: Optional[int] = None
    order_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    total_amount: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_map(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "total_amount": self.total_amount,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }



class UserOrderModel(BaseModel):
    status: Optional[str] = "pending"
    type: Optional[str] = "regular"
    total_amount: Optional[float] = None
    items: Optional[List[UserOrderItem]] = []
