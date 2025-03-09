from typing import List, Optional, Any, Coroutine
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.databases.postgres import get_general_session
from app.api.models.product import Size
from app.api.schemas.product.size import (
    SizeCreateSchema,
    SizeUpdateSchema,
    SizeResponseSchema,
    SizeCreateResponseSchema,
)


class SizeRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def get_sizes(
        self, warehouse_id: int | None, language
    ) -> List[SizeResponseSchema]:
        if warehouse_id is not None:
            result = await self.__session.execute(
                select(Size).where(Size.warehouse_id == warehouse_id)
            )
        else:
            result = await self.__session.execute(select(Size))
        sizes = result.scalars().all()

        return [
            SizeResponseSchema(
                id=s.id,
                size=s.size,
                description=s.description.get(language) if s.description else "",
                warehouse_id=s.warehouse_id,
            )
            for s in sizes
        ]

    async def get_size_by_id(
        self, size_id: int, language
    ) -> Optional[SizeResponseSchema] | SizeCreateResponseSchema:
        result = await self.__session.execute(select(Size).where(Size.id == size_id))
        s = result.scalar_one_or_none()
        if not s:
            return None

        if language is not None:
            return SizeResponseSchema(
                id=s.id,
                size=s.size,
                description=s.description.get(language) if s.description else "",
                warehouse_id=s.warehouse_id,
            )
        return SizeCreateResponseSchema.model_validate(s)

    async def create_size(self, data) -> SizeCreateResponseSchema:
        size_obj = Size(**data)
        self.__session.add(size_obj)
        await self.__session.commit()
        await self.__session.refresh(size_obj)
        return SizeCreateResponseSchema(
            id=size_obj.id,
            description=size_obj.description,
            size=size_obj.size,
            warehouse_id=size_obj.warehouse_id,
        )

    async def update_size(
        self, size_id: int, data: SizeUpdateSchema
    ) -> SizeCreateResponseSchema:
        result = await self.__session.execute(select(Size).where(Size.id == size_id))
        s = result.scalar_one_or_none()
        if not s:
            raise HTTPException(404, "Size not found")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(s, field, value)
        self.__session.add(s)
        await self.__session.commit()
        await self.__session.refresh(s)
        return SizeCreateResponseSchema.model_validate(s)

    async def delete_size(self, size_id: int) -> None:
        result = await self.__session.execute(select(Size).where(Size.id == size_id))
        s = result.scalar_one_or_none()
        if not s:
            raise HTTPException(404, "Size not found")

        await self.__session.delete(s)
        await self.__session.commit()
