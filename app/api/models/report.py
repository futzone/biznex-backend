from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.core.models.base import Base


class ReportStatusEnum(str, PyEnum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    rejected = "rejected"


class Report(Base):

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="reports")

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(ReportStatusEnum), nullable=False)
    created_at = Column(DateTime, default=func.now())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Report id={self.id} title={self.title} status={self.status} user_id={self.user_id}>"
