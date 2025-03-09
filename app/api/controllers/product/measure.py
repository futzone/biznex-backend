# app/api/controllers/product/measure.py
from typing import List
from fastapi import Depends, HTTPException, status

from app.api.repositories.product.measure import MeasureRepository
from app.api.schemas.product.measure import (
    MeasureCreateSchema,
    MeasureUpdateSchema,
    MeasureResponseSchema,
)


class MeasureController:
    def __init__(self, repo: MeasureRepository = Depends()):
        self.__repo = repo

    async def get_measures(self) -> List[MeasureResponseSchema]:
        return await self.__repo.get_measures()

    async def get_measure_by_id(self, measure_id: int) -> MeasureResponseSchema:
        measure_data = await self.__repo.get_measure_by_id(measure_id)
        if not measure_data:
            raise HTTPException(404, "Measure not found")
        return measure_data

    async def create_measure(self, data: MeasureCreateSchema) -> MeasureResponseSchema:
        return await self.__repo.create_measure(data)

    async def update_measure(
        self, measure_id: int, data: MeasureUpdateSchema
    ) -> MeasureResponseSchema:
        return await self.__repo.update_measure(measure_id, data)

    async def delete_measure(self, measure_id: int) -> None:
        return await self.__repo.delete_measure(measure_id)
