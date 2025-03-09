from typing import List, Any, Coroutine
from fastapi import Depends, HTTPException

from app.api.repositories.product.size import SizeRepository
from app.api.repositories.warehouse import WarehouseRepository
from app.api.schemas.product.size import (
    SizeCreateSchema,
    SizeUpdateSchema,
    SizeResponseSchema,
    SizeCreateResponseSchema,
)

from app.api.utils.check_language import check_language
from app.api.utils.translator import translate_text


class SizeController:
    def __init__(
        self,
        size_repository: SizeRepository = Depends(),
        warehouse_repository: WarehouseRepository = Depends(),
    ):
        self.__size_repository = size_repository
        self.__warehouse_repository = warehouse_repository

    async def get_sizes(
        self, warehouse_id: int | None, language
    ) -> List[SizeResponseSchema]:
        return await self.__size_repository.get_sizes(warehouse_id, language=language)

    async def get_size_by_id(
        self, size_id: int, language
    ) -> SizeResponseSchema | SizeCreateResponseSchema:
        await check_language(language)
        s = await self.__size_repository.get_size_by_id(size_id, language=language)
        if not s:
            raise HTTPException(404, "Size not found")
        return s

    async def create_size(self, data: SizeCreateSchema) -> SizeCreateResponseSchema:
        wh = await self.__warehouse_repository.get_warehouse_by_id(data.warehouse_id)
        if not wh:
            raise HTTPException(404, "Warehouse not found")

        new_data = {
            "size": data.size,
            "description": (
                await translate_text(data.description) if data.description else {}
            ),
            "warehouse_id": data.warehouse_id,
        }

        return await self.__size_repository.create_size(new_data)

    async def update_size(
        self, size_id: int, data: SizeUpdateSchema
    ) -> SizeCreateResponseSchema:
        data.description = (
            await translate_text(data.description) if data.description else {}
        )
        return await self.__size_repository.update_size(size_id, data)

    async def delete_size(self, size_id: int) -> None:
        return await self.__size_repository.delete_size(size_id)
