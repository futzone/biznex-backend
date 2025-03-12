# app/api/repositories/product/color.py
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.utils.translator import translate_text
from app.core.databases.postgres import get_general_session
from app.api.models.product import Color
from app.api.schemas.product.color import (
    ColorCreateSchema,
    ColorLanguageResponseSchema,
    ColorUpdateSchema,
    ColorResponseSchema,
)


class ColorRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def get_colors(self, language: str) -> List[ColorResponseSchema] | List[ColorLanguageResponseSchema]:
        result = await self.__session.execute(select(Color))
        items = result.scalars().all()

        if language is not None:
            return [
                ColorResponseSchema(
                    id=item.id,
                    name=(item.name.get('uz') if item.name.get('uz') is not None else item.name.get('en')) if (item.name.get('uz') if item.name.get('uz') is not None else item.name.get(
                        'en')) is not None else (f"{item.name}"),
                    hex_code=item.hex_code,
                )
                for item in items
            ]

        return [ColorLanguageResponseSchema.model_validate(c) for c in items]

    async def get_color_by_id(self, color_id: int, language: str) -> Optional[ColorResponseSchema] | ColorLanguageResponseSchema:
        result = await self.__session.execute(select(Color).where(Color.id == color_id))
        color_obj = result.scalar_one_or_none()
        if not color_obj:
            return None

        if language is not None:
            return ColorLanguageResponseSchema(
                id=color_obj.id,
                name=color_obj.name.get(language),
                hex_code=color_obj.hex_code,
            )

        return ColorLanguageResponseSchema.model_validate(color_obj)

    async def create_color(self, data: ColorCreateSchema) -> ColorLanguageResponseSchema:

        new_data = {
            "name": await translate_text(data.name),
            "hex_code": data.hex_code,
        }

        color_obj = Color(**new_data)
        self.__session.add(color_obj)
        await self.__session.commit()
        await self.__session.refresh(color_obj)
        return ColorLanguageResponseSchema.model_validate(color_obj)

    async def update_color(
            self, color_id: int, data: ColorUpdateSchema
    ) -> ColorLanguageResponseSchema:
        result = await self.__session.execute(select(Color).where(Color.id == color_id))
        color_obj = result.scalar_one_or_none()
        if not color_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Color not found"
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(color_obj, field, value)

        self.__session.add(color_obj)
        await self.__session.commit()
        await self.__session.refresh(color_obj)
        return ColorLanguageResponseSchema.model_validate(color_obj)

    async def delete_color(self, color_id: int) -> None:
        result = await self.__session.execute(select(Color).where(Color.id == color_id))
        color_obj = result.scalar_one_or_none()
        if not color_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Color not found"
            )

        await self.__session.delete(color_obj)
        await self.__session.commit()
