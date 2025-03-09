from typing import Sequence, Optional
from fastapi import Depends, HTTPException

from app.api.repositories.auth import UserRepository
from app.api.repositories.device.device import DeviceRepository
from app.api.schemas.device.device import (
    DeviceCreateSchema,
    DeviceResponseSchema,
)


class DeviceController:
    def __init__(self,
                 device_repository: DeviceRepository = Depends(),
                 user_repository: UserRepository = Depends(),
                 ):
        self.__device_repository = device_repository
        self.__user_repository = user_repository

    async def get_all_devices(
            self, offset: int = 0, limit: int = 10, search: Optional[str] = None
    ) -> Sequence[DeviceResponseSchema]:
        return await self.__device_repository.get_all_devices(offset=offset, limit=limit, search=search)

    async def get_device_by_id(self, device_id: int) -> DeviceResponseSchema:
        device = await self.__device_repository.get_device_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        return device

    async def get_device_by_user_id(self, device_id: int | None, user_id: int, limit, offset) -> Sequence[DeviceResponseSchema]:
        user = await self.__user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return await self.__device_repository.get_device_by_user_id(device_id, user_id,limit,offset)

    async def create_device(self, device: DeviceCreateSchema) -> DeviceResponseSchema:
        return await self.__device_repository.create_device(device)

    async def delete_device(self, device_id: int):
        device = await self.__device_repository.get_device_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        return await self.__device_repository.delete_device(device_id)
