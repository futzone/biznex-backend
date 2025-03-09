from typing import List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.databases.postgres import get_general_session
from app.api.models.product import Measure
from app.api.schemas.product.measure import (
    MeasureCreateSchema,
    MeasureUpdateSchema,
    MeasureResponseSchema,
)


class MeasureRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def get_measures(self) -> List[MeasureResponseSchema]:
        result = await self.__session.execute(select(Measure))
        items = result.scalars().all()
        return [MeasureResponseSchema.model_validate(m) for m in items]

    async def get_measure_by_id(
        self, measure_id: int
    ) -> Optional[MeasureResponseSchema]:
        result = await self.__session.execute(
            select(Measure).where(Measure.id == measure_id)
        )
        measure_obj = result.scalar_one_or_none()
        if not measure_obj:
            return None
        return MeasureResponseSchema.model_validate(measure_obj)

    async def create_measure(self, data: MeasureCreateSchema) -> MeasureResponseSchema:
        measure_obj = Measure(**data.model_dump())
        self.__session.add(measure_obj)
        await self.__session.commit()
        await self.__session.refresh(measure_obj)
        return MeasureResponseSchema.model_validate(measure_obj)

    async def update_measure(
        self, measure_id: int, data: MeasureUpdateSchema
    ) -> MeasureResponseSchema:
        result = await self.__session.execute(
            select(Measure).where(Measure.id == measure_id)
        )
        measure_obj = result.scalar_one_or_none()
        if not measure_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Measure not found"
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(measure_obj, field, value)

        self.__session.add(measure_obj)
        await self.__session.commit()
        await self.__session.refresh(measure_obj)
        return MeasureResponseSchema.model_validate(measure_obj)

    async def delete_measure(self, measure_id: int) -> None:
        result = await self.__session.execute(
            select(Measure).where(Measure.id == measure_id)
        )
        measure_obj = result.scalar_one_or_none()
        if not measure_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Measure not found"
            )

        await self.__session.delete(measure_obj)
        await self.__session.commit()
