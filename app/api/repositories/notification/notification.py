from typing import Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.models.notification import Notification
from app.api.schemas.notification.notification import (
    NotificationCreateSchema,
    NotificationResponseSchema,
)
from app.core.databases.postgres import get_general_session


class NotificationRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.session = session

    async def create_notification(
        self, data: NotificationCreateSchema, image_path: Optional[str] = None
    ) -> NotificationResponseSchema:
        notification = Notification(
            title=data.title,
            body=data.body,
            type=data.type,
            image=image_path,
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return NotificationResponseSchema.model_validate(notification)

    async def get_notification_by_id(
        self, notification_id: int
    ) -> Optional[Notification]:
        result = await self.session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def list_notifications(self) -> list[NotificationResponseSchema]:
        result = await self.session.execute(select(Notification))
        notifications = result.scalars().all()
        return [NotificationResponseSchema.model_validate(n) for n in notifications]
