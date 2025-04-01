from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Boolean,
    Float,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship
from app.core.models.base import Base
from utils.time_utils import now_time


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)
    courier_note = Column(String(255), nullable=False)
    name_of_recipient = Column(String(50), nullable=False)
    phone_number_of_recipient = Column(String(15), nullable=False)
    is_main = Column(Boolean, default=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="addresses")

    created_at = Column(DateTime, default=now_time())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=now_time(), onupdate=now_time())

    def __repr__(self):
        return f"<Address id={self.id} title={self.title}>"
