from typing import List, Sequence
from fastapi import Depends, HTTPException, status

from app.api.constants.languages import languages, languages_error_message
from app.api.repositories.product.product_information import (
    ProductInformationRepository,
)
from app.api.repositories.warehouse import WarehouseRepository
from app.api.schemas.product.product_information import (
    ProductInformationCreateSchema,
    ProductInformationUpdateSchema,
    ProductInformationResponseSchema,
    ProductInformationLanguageResponseSchema,
)
from app.api.utils.check_language import check_language


class ProductInformationController:
    def __init__(
        self,
        info_repository: ProductInformationRepository = Depends(),
        warehouse_repository: WarehouseRepository = Depends(),
    ):
        self.__info_repository = info_repository
        self.__warehouse_repository = warehouse_repository

    async def get_all_info(
        self, warehouse_id: int | None, language
    ) -> Sequence[
        ProductInformationResponseSchema | ProductInformationLanguageResponseSchema
    ]:
        await check_language(language)
        if warehouse_id:
            warehouse = await self.__warehouse_repository.get_warehouse_by_id(
                warehouse_id
            )
            if warehouse is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Warehouse not found",
                )
        return await self.__info_repository.get_all_info(warehouse_id, language)

    async def get_info_by_id(
        self, info_id: int, language: str | None
    ) -> ProductInformationResponseSchema | ProductInformationLanguageResponseSchema:
        await check_language(language)
        info = await self.__info_repository.get_info_by_id(info_id, language)
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ProductInformation not found",
            )
        if language is None:
            return ProductInformationLanguageResponseSchema.model_validate(info)
        return ProductInformationResponseSchema.model_validate(info)

    async def create_info(
        self, data: ProductInformationCreateSchema
    ) -> ProductInformationLanguageResponseSchema:
        current_warehouse = await self.__warehouse_repository.get_warehouse_by_id(
            data.warehouse_id
        )
        if current_warehouse is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Warehouse not found with {data.warehouse_id} id",
            )
        return await self.__info_repository.create_info(data)

    async def update_info(
        self, info_id: int, data: ProductInformationUpdateSchema
    ) -> ProductInformationLanguageResponseSchema:
        return await self.__info_repository.update_info(info_id, data)

    async def delete_info(self, info_id: int) -> None:
        return await self.__info_repository.delete_info(info_id)
