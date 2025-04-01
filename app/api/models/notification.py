from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, func, ForeignKey
from app.core.models.base import Base
from app.core.models.enums import NotificationStatus
from sqlalchemy.orm import relationship

from utils.time_utils import now_time


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)
    body = Column(Text, nullable=True)
    image = Column(String(255), nullable=True)

    type = Column(Enum(NotificationStatus), default=NotificationStatus.INFO)
    created_at = Column(DateTime, default=now_time())

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="notifications")

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    order = relationship("Order", back_populates="notifications")

    created_at = Column(DateTime, default=now_time())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=now_time(), onupdate=now_time())


def __repr__(self):
    return f"<Notification id={self.id} title={self.title}>"
