from datetime import datetime, timedelta
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from app.api.models.order import AdminOrder
from app.core.models.base import Base
from utils.time_utils import now_time
from .warehouse import admin_warehouse_roles


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False)
    message = Column(String, nullable=False)
    is_bot = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=now_time(), index=True)

    user = relationship("AdminUser", back_populates="chats")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(50), nullable=False)
    phone_number = Column(String(15), nullable=False)
    password = Column(String(255), nullable=False)
    profile_picture = Column(String(255), nullable=True, default="None")
    is_active = Column(Boolean, default=False)

    sms_codes = relationship("SMSCode", back_populates="user")
    orders = relationship("Order", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    addresses = relationship("Address", back_populates="user")
    ratings = relationship("Rating", back_populates="user")
    wishlists = relationship("Wishlist", back_populates="user")
    reports = relationship("Report", back_populates="user")

    devices = relationship("Device", back_populates="user")

    def __repr__(self):
        return f"<User id={self.id} full_name={self.full_name}>"

    def __str__(self):
        return self.full_name

    def __eq__(self, other):
        return self.id == other.id


class UserDB(Base):
    __tablename__ = "user_db"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)


class SMSCode(Base):
    __tablename__ = "sms_codes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    code = Column(String(6), nullable=False)
    created_at = Column(DateTime, default=now_time())
    expired_at = Column(
        DateTime, default=lambda: now_time() + timedelta(minutes=10)
    )
    is_used = Column(Boolean, default=False)

    user = relationship("User", back_populates="sms_codes")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(50), nullable=False)
    phone_number = Column(String(15), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    profile_picture = Column(String(255), nullable=True)
    is_global_admin = Column(Boolean, default=False)

    created_at = Column(DateTime, default=now_time())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=now_time(), onupdate=now_time())

    orders = relationship("AdminOrder", foreign_keys=[AdminOrder.by], back_populates="admin")
    seller_orders = relationship("AdminOrder", foreign_keys=[AdminOrder.seller], back_populates="seller_admin")

    warehouse_roles = relationship(
        "AdminWarehouse", secondary=admin_warehouse_roles, back_populates="admins"
    )
    chats = relationship("ChatHistory", back_populates="user")
