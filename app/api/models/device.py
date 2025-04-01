from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, func, Boolean
from sqlalchemy.orm import relationship

from app.core.models.base import Base
from utils.time_utils import now_time


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    key = Column(String(255), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip_address = Column(String(15), nullable=True)
    device_name = Column(String(50), nullable=True)
    device_info = Column(String(255), nullable=True)

    user = relationship("User", back_populates="devices")
    created_at = Column(DateTime, default=now_time())
    updated_at = Column(DateTime, default=now_time(), onupdate=now_time())

    def __repr__(self):
        return f"<Device id={self.id} key={self.key}>"
