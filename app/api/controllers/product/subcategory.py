from typing import List, Sequence, Optional
from fastapi import Depends, HTTPException, status

from app.api.repositories.product.category import CategoryRepository
from app.api.repositories.product.subcategory import SubcategoryRepository
from app.api.schemas.product.subcategory import (
    SubcategoryCreateSchema,
    SubcategoryUpdateSchema,
    SubcategoryResponseSchema,
    SubcategoryCreateResponseSchema,
)

from app.api.utils.translator import translate_text
from app.api.utils.check_language import check_language


class SubcategoryController:
    def __init__(
            self,
            subcategory_repository: SubcategoryRepository = Depends(),
            category_repository: CategoryRepository = Depends(),
    ):
        self.__subcategory_repository = subcategory_repository
        self.__category_repository = category_repository

    async def get_subcategories(
            self, category_id: Optional[int], language, warehouse_id
    ) -> Sequence[SubcategoryResponseSchema] | SubcategoryCreateResponseSchema:
        if category_id is not None:
            res = await self.__category_repository.get_warehouse_category_by_id(
                category_id, language, warehouse_id
            )
            if res is None:
                raise HTTPException(
                    status_code=404, detail="Category not found")

        return await self.__subcategory_repository.get_subcategories(
            category_id, language
        )

    async def get_subcategory_by_id(
            self, subcategory_id: int, language: str
    ) -> Optional[SubcategoryResponseSchema]:
        await check_language(language)
        return await self.__subcategory_repository.get_subcategory_by_id(
            subcategory_id, language=language
        )

    async def create_subcategory(
            self, data: SubcategoryCreateSchema
    ) -> SubcategoryCreateResponseSchema:

        translated_name = {
            "uz": data.name,
            "ru": data.name,
            "en": data.name,
        }
        translated_description = (
            await translate_text(data.description) if data.description else {}
        )
        category_id = data.category_id

        return await self.__subcategory_repository.create_subcategory(
            translated_name, translated_description, category_id
        )

    async def update_subcategory(
            self, subcategory_id: int, data: SubcategoryUpdateSchema
    ) -> SubcategoryCreateResponseSchema:

        data.name = await translate_text(data.name)
        data.description = (
            await translate_text(data.description
                                 ) if data.description else {}
        )

        return await self.__subcategory_repository.update_subcategory(
            subcategory_id, data
        )

    async def delete_subcategory(self, subcategory_id: int) -> None:
        return await self.__subcategory_repository.delete_subcategory(subcategory_id)
