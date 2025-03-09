from typing import Sequence, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from app.core.databases.postgres import get_general_session
from app.api.models.device import Device
from app.api.models.user import User
from app.api.schemas.device.device import (
    DeviceCreateSchema,
    DeviceResponseSchema,
)


class DeviceRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def get_all_devices(
            self, offset: int = 0, limit: int = 10, search: Optional[str] = None
    ) -> list[DeviceResponseSchema]:
        if search:
            query = (
                select(Device)
                .join(User)
                .where(
                    or_(
                        Device.device_name.ilike(f"%{search}%"),
                        Device.key.ilike(f"%{search}%"),
                        Device.ip_address.ilike(f"%{search}%"),
                        User.full_name.ilike(f"%{search}%")
                    )
                )
                .offset(offset)
                .limit(limit)
            )
        else:
            query = select(Device).offset(offset).limit(limit)

        result = await self.__session.execute(query)
        devices = result.scalars().all()
        return [DeviceResponseSchema.model_validate(device) for device in devices]

    async def get_device_by_id(self, device_id: int) -> Optional[DeviceResponseSchema]:
        query = select(Device).where(Device.id == device_id)
        result = await self.__session.execute(query)
        device = result.scalar_one_or_none()
        if device:
            return DeviceResponseSchema.model_validate(device)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    async def get_device_by_user_id(self, device_id: int, user_id: int, limit, offset) -> Sequence[
        DeviceResponseSchema]:
        if device_id is None:
            query = select(Device).where(Device.user_id == user_id).limit(limit).offset(offset)
        else:
            query = select(Device).where(Device.id == device_id, Device.user_id == user_id).limit(limit).offset(offset)
        result = await self.__session.execute(query)
        devices = result.scalars().all()
        if not devices:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        return [DeviceResponseSchema.model_validate(device) for device in devices]

    async def create_device(self, device_data: DeviceCreateSchema) -> DeviceResponseSchema:
        new_device = Device(
            user_id=device_data.user_id,
            key=device_data.key,
            ip_address=device_data.ip_address,
            device_name=device_data.device_name,
            device_info=device_data.device_info,
        )
        self.__session.add(new_device)
        await self.__session.commit()
        await self.__session.refresh(new_device)
        return DeviceResponseSchema.model_validate(new_device)

    async def delete_device(self, device_id: int):
        query = select(Device).where(Device.id == device_id)
        result = await self.__session.execute(query)
        device = result.scalar_one_or_none()
        if device:
            await self.__session.delete(device)
            await self.__session.commit()
            return
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
