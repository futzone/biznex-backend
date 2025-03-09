from typing import List
from fastapi import Depends, HTTPException, status

from app.api.repositories.product.color import ColorRepository
from app.api.schemas.product.color import (
    ColorCreateSchema,
    ColorLanguageResponseSchema,
    ColorUpdateSchema,
    ColorResponseSchema,
)
from app.api.utils.check_language import check_language


class ColorController:
    def __init__(self, repo: ColorRepository = Depends()):
        self.__repo = repo

    async def get_colors(self, language: str) -> List[ColorResponseSchema] | ColorLanguageResponseSchema:
        await check_language(language)
        return await self.__repo.get_colors(language)

    async def get_color_by_id(self, color_id: int, language: str) -> ColorResponseSchema | ColorLanguageResponseSchema:
        await check_language(language)
        color_data = await self.__repo.get_color_by_id(color_id, language)
        if not color_data:
            raise HTTPException(status_code=404, detail="Color not found")
        return color_data

    async def create_color(self, data: ColorCreateSchema) -> ColorLanguageResponseSchema:
        return await self.__repo.create_color(data)

    async def update_color(
        self, color_id: int, data: ColorUpdateSchema
    ) -> ColorLanguageResponseSchema:
        return await self.__repo.update_color(color_id, data)

    async def delete_color(self, color_id: int) -> None:
        return await self.__repo.delete_color(color_id)
