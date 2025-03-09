# app/api/controllers/notification/notification.py

import os
import uuid
from typing import Optional, Sequence
from fastapi import Depends, HTTPException, status
from fastapi import UploadFile
from pydantic import ValidationError

from app.core.utils.firebase import (
    send_push_notification,
    send_push_notification_to_topic,
)
from app.api.repositories.notification.notification import NotificationRepository
from app.api.repositories.device.device import DeviceRepository
from app.api.schemas.notification.notification import (
    NotificationCreateSchema,
    NotificationResponseSchema,
)


class NotificationController:
    def __init__(
        self,
        notification_repo: NotificationRepository = Depends(),
        device_repo: DeviceRepository = Depends(),
    ):
        self.notification_repo = notification_repo
        self.device_repo = device_repo

    async def create_notification_with_image(
        self,
        title: str,
        body: str,
        type_str: str,
        image_file: Optional[UploadFile] = None,
    ) -> NotificationResponseSchema:
        """
        1) Save image (if provided)
        2) Create Notification in DB
        """
        image_path = None
        # 1) Save image if any
        if image_file:
            unique_filename = f"{uuid.uuid4()}_{image_file.filename}".replace(
                " ", "_")
            image_path = os.path.join("media", "notification", unique_filename)
            os.makedirs(os.path.dirname(image_path),
                        exist_ok=True)  # ensure folders

            try:
                with open(image_path, "wb") as buffer:
                    buffer.write(await image_file.read())
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error saving image: {str(e)}",
                )

        # 2) Validate data with Pydantic
        try:
            data = NotificationCreateSchema(
                title=title,
                body=body,
                type=type_str,  # e.g. "success" / "info" / "danger" / "warning"
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation error: {str(e)}",
            )

        # 3) Create in DB
        return await self.notification_repo.create_notification(data, image_path)

    async def send_notification_to_user(self, notification_id: int, user_id: int):
        notification = await self.notification_repo.get_notification_by_id(
            notification_id
        )
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        devices = await self.device_repo.get_devices_for_user(user_id)
        if not devices:
            # Could be 200 OK or 404, depending on your needs
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No devices found for this user",
            )

        for device in devices:
            if device.key:
                send_push_notification(
                    registration_token=device.key,
                    title=notification.title,
                    body=notification.body or "",
                    image=notification.image or "",
                )

        return {"message": "Notification sent to user's devices"}

    async def send_notification_to_all(
        self, notification_id: int, topic: str = "all_users"
    ):
        notification = await self.notification_repo.get_notification_by_id(
            notification_id
        )
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )
        response_id = send_push_notification_to_topic(
            topic=topic,
            title=notification.title,
            body=notification.body or "",
            image=notification.image or "",
        )
        return {
            "message": f"Notification sent to topic={topic}",
            "fcm_response": response_id,
        }

    async def list_notifications(self) -> Sequence[NotificationResponseSchema]:
        return await self.notification_repo.list_notifications()
