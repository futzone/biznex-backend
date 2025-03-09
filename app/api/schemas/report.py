from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


# Enum for report status
class ReportStatusEnum(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    rejected = "rejected"


# Base schema for common fields
class ReportBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[ReportStatusEnum] = ReportStatusEnum.pending


# Schema for creating a new report
class ReportCreate(ReportBase):
    user_id: int


# Schema for updating a report
class ReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ReportStatusEnum] = None


# Schema for returning report data
class Report(ReportBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
