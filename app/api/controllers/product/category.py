from typing import List, Sequence, Optional
from fastapi import Depends, HTTPException

from app.api.repositories.product.category import CategoryRepository
from app.api.schemas.product.category import (
    CategoryCreateSchema,
    CategoryUpdateSchema,
    CategoryResponseSchema,
    CategoryCreateResponseSchema,
)

from app.api.utils.check_language import check_language
from app.api.utils.translator import translate_text


class CategoryController:
    def __init__(self, category_repository: CategoryRepository = Depends()):
        self.__category_repository = category_repository

    async def get_warehouse_categories(self, warehouse_id, language):
        await check_language(language)
        if warehouse_id:
            return await self.__category_repository.get_warehouse_categories(warehouse_id, language)

        return await self.__category_repository.get_categories(language)

    async def get_category_by_id(
        self, warehouse_id, category_id: int, language: str
    ) -> List[CategoryResponseSchema]:

        await check_language(language)
        if warehouse_id:
            return await self.__category_repository.get_warehouse_category_by_id(
                warehouse_id, category_id, language
            )
        return await self.__category_repository.get_category_by_id(category_id, language)

    async def create_category(
        self, warehouse_id: int, data: CategoryCreateSchema
    ) -> CategoryCreateResponseSchema:

        translated_name = await translate_text(data.name)
        translated_description = (
            await translate_text(data.description) if data.description else {}
        )
        image = data.image

        return await self.__category_repository.create_category(
            warehouse_id, translated_name, translated_description, image
        )

    async def update_category(
        self, category_id: int, data: CategoryUpdateSchema
    ) -> CategoryCreateResponseSchema:
        data.name = await translate_text(data.name)
        data.description = (
            await translate_text(data.description) if data.description else {}
        )
        return await self.__category_repository.update_category(category_id, data)

    async def delete_category(self, category_id: int) -> None:
        try:
            return await self.__category_repository.delete_category(category_id)
        except Exception as e:
            raise HTTPException(
                status_code=404, detail=f"Categoriyani o'chira olmaysiz chunki u boshqa subcategoriyga bog'langan: {e}")
