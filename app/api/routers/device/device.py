from typing import Sequence, Optional
from fastapi import APIRouter, Depends, status
from fastapi.params import Query

from app.api.schemas.device.device import DeviceCreateSchema, DeviceResponseSchema
from app.api.controllers.device.device import DeviceController

router = APIRouter()

@router.get("/", response_model=Sequence[DeviceResponseSchema])
async def get_all_devices(
        controller: DeviceController = Depends(),
        offset: int = Query(0, ge=0),
        limit: int = Query(10, le=100),
        search: Optional[str] = Query(None)
) -> Sequence[DeviceResponseSchema]:
    return await controller.get_all_devices(offset=offset, limit=limit, search=search)


@router.get("/{device_id}", response_model=DeviceResponseSchema)
async def get_device_by_id(
        device_id: int, controller: DeviceController = Depends()
) -> DeviceResponseSchema:
    return await controller.get_device_by_id(device_id)


@router.get("/{user_id}/devices", response_model=Sequence[DeviceResponseSchema])
async def get_device_by_user_id(
        user_id: int,
        device_id: Optional[int] = None,
        limit: int = Query(10, le=100),
        offset: int = Query(0, ge=0),
        controller: DeviceController = Depends()
) -> Sequence[DeviceResponseSchema]:
    return await controller.get_device_by_user_id(device_id, user_id, limit, offset)


@router.post("/", response_model=DeviceResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_device(
        device: DeviceCreateSchema, controller: DeviceController = Depends()
) -> DeviceResponseSchema:
    return await controller.create_device(device)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: int, controller: DeviceController = Depends()):
    return await controller.delete_device(device_id)
