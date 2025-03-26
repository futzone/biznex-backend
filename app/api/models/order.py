from datetime import datetime

from sqlalchemy import DECIMAL, Column, Integer, Float, DateTime, ForeignKey, func, text, String, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM
from app.api.schemas.order import OrderStatusEnum, OrderTypeEnum
from app.core.models.base import Base
from app.core.models.enums import AdminOrderStatusEnum, PaymentMethodEnum


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="orders")

    status = Column(ENUM(OrderStatusEnum, name="order_status_enum"), nullable=False)
    type = Column(ENUM(OrderTypeEnum, name="order_type_enum"), nullable=False)

    total_amount = Column(Float, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=text("TIMEZONE('utc', now())")
    )
    updated_at = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)

    items = relationship("OrderItem", back_populates="order")
    notifications = relationship("Notification", back_populates="order")

    def __repr__(self):
        return f"<Order id={self.id} user_id={self.user_id} status={self.status}>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    quantity = Column(Integer, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    total_amount = Column(Float, nullable=False)

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    order = relationship("Order", back_populates="items")

    created_at = Column(
        DateTime(timezone=True), server_default=text("TIMEZONE('utc', now())")
    )

    product = relationship("Product", back_populates="orders")

    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<OrderItem id={self.id} order_id={self.order_id}>"


class AdminOrder(Base):
    __tablename__ = "admin_orders"
    id = Column(Integer, primary_key=True)
    by = Column(Integer, ForeignKey("admin_users.id"), nullable=False)
    seller = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    status = Column(ENUM(AdminOrderStatusEnum, name="admin_order_status_enum"), nullable=False, default="opened")
    user_name = Column(String(255), nullable=True)
    user_phone = Column(String(50), nullable=True)
    total_amount = Column(DECIMAL(10, 2), default=0)
    total_amount_with_discount = Column(DECIMAL(10, 2), default=0, nullable=True)
    notes = Column(Text, nullable=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    payment_type = Column(ENUM(PaymentMethodEnum, name="payment_type"), nullable=False, default="cash")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    canceled_at = Column(DateTime, default=None, nullable=True)

    admin = relationship("AdminUser", foreign_keys=[by], back_populates="orders")
    seller_admin = relationship("AdminUser", foreign_keys=[seller], back_populates="seller_orders")
    items = relationship("AdminOrderItem", back_populates="order", cascade="all, delete-orphan")
    product_variants = relationship("AdminOrderItem", back_populates="order", overlaps="items", viewonly=True)
    warehouse = relationship("Warehouse", back_populates="admin_order")

    def __repr__(self):
        return f"<AdminOrder id={self.id} by={self.by} status={self.status}>"


class AdminOrderItem(Base):
    __tablename__ = "admin_order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("admin_orders.id"), nullable=False)
    product_variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
    quantity = Column(Numeric, nullable=False, default=1)
    notes = Column(Text, nullable=True)
    price_per_unit = Column(DECIMAL(10, 2), nullable=False)
    price_with_discount = Column(DECIMAL(10, 2), nullable=True)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    total_amount_with_discount = Column(DECIMAL(10, 2), nullable=True, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    order = relationship("AdminOrder", back_populates="items")
    product_variant = relationship("ProductVariant")

    def calculate_total(self):
        return self.quantity * self.price_per_unit

    def calculate_total_with_discount(self):
        return self.quantity * (self.price_with_discount or self.price_per_unit)

    def __repr__(self):
        return f"<AdminOrderItem id={self.id} order_id={self.order_id}>"
