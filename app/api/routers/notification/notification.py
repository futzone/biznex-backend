from typing import Sequence
from fastapi import APIRouter, Depends, status, File, Form, UploadFile, HTTPException

from app.api.controllers.notification.notification import NotificationController
from app.api.schemas.notification.notification import (
    NotificationResponseSchema,
)

router = APIRouter()


@router.post(
    "/", response_model=NotificationResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_notification(
    title: str = Form(...),
    body: str = Form(""),
    # e.g. "success", "info", "danger", "warning"
    type_str: str = Form("info"),
    image: UploadFile = File(None),
    controller: NotificationController = Depends(),
) -> NotificationResponseSchema:
    return await controller.create_notification_with_image(title, body, type_str, image)


@router.post("/{notification_id}/send-to-user/", status_code=status.HTTP_200_OK)
async def send_notification_to_user(
    notification_id: int,
    user_id: int = Form(...),
    controller: NotificationController = Depends(),
):
    """
    Send the given notification to all devices belonging to `user_id`.
    """
    return await controller.send_notification_to_user(notification_id, user_id)


@router.post("/{notification_id}/send-to-all/", status_code=status.HTTP_200_OK)
async def send_notification_to_all(
    notification_id: int,
    controller: NotificationController = Depends(),
):
    return await controller.send_notification_to_all(notification_id, topic="all_users")


@router.get(
    "/",
    response_model=Sequence[NotificationResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def list_notifications(controller: NotificationController = Depends()):
    return await controller.list_notifications()
