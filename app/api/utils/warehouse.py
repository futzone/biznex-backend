from fastapi import HTTPException, status, Form
from app.core.models.enums import WarehouseApplicationStatus


async def check_status(status_value: str = Form(None), is_post=False):
    if is_post and not status_value:
        return WarehouseApplicationStatus.PENDING
    if status_value:
        status_value = status_value.lower()
        if status_value == "pending":
            return WarehouseApplicationStatus.PENDING
        if status_value == "accepted":
            return WarehouseApplicationStatus.ACCEPTED
        if status_value == "rejected":
            return WarehouseApplicationStatus.REJECTED
        if is_post:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status value is invalid",
            )
        return WarehouseApplicationStatus.PENDING
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Status value is required",
    )
