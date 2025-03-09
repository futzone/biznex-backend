from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.api.models.notification import NotificationStatus


class NotificationCreateSchema(BaseModel):
    title: str
    body: Optional[str] = None
    type: Optional[NotificationStatus] = NotificationStatus.INFO


class NotificationResponseSchema(NotificationCreateSchema):
    id: int
    image: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
