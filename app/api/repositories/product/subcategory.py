from typing import List, Optional, Sequence
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.databases.postgres import get_general_session
from app.api.models.product import Subcategory
from app.api.schemas.product.subcategory import (
    SubcategoryCreateSchema,
    SubcategoryUpdateSchema,
    SubcategoryResponseSchema,
    SubcategoryCreateResponseSchema,
)


class SubcategoryRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def get_subcategories(
            self, category_id: int | None, language: str
    ) -> Sequence[SubcategoryResponseSchema]:

        if category_id is not None:
            result = await self.__session.execute(
                select(Subcategory).where(Subcategory.category_id == category_id)
            )
        else:
            result = await self.__session.execute(select(Subcategory))
        subcategories = result.scalars().all()
        return [
            SubcategoryResponseSchema(
                id=subcategory.id,
                name=subcategory.name.get(language),
                description=(
                    subcategory.description.get(language)
                    if subcategory.description
                    else ""
                ),
                category_id=subcategory.category_id,
            )
            for subcategory in subcategories
        ]

    async def get_subcategory_by_id(
            self,
            subcategory_id: int,
            language: str,
    ) -> Optional[SubcategoryResponseSchema]:
        result = await self.__session.execute(
            select(Subcategory).where(Subcategory.id == subcategory_id)
        )
        subcategory = result.scalar_one_or_none()
        if not subcategory:
            return None

        if language is not None:
            return SubcategoryResponseSchema(
                id=subcategory.id,
                name=subcategory.name.get(language, ""),
                description=(
                    subcategory.description.get(language)
                    if subcategory.description
                    else None
                ),
                category_id=subcategory.category_id,
            )
        return SubcategoryCreateResponseSchema.model_validate(subcategory)

    async def create_subcategory(
            self,
            translated_name,
            translated_description,
            category_id,
    ) -> SubcategoryCreateResponseSchema:

        data = {
            "name": translated_name,
            "description": translated_description,
            "category_id": category_id,
        }

        subcategory_instance = Subcategory(**data)
        self.__session.add(subcategory_instance)
        await self.__session.commit()
        await self.__session.refresh(subcategory_instance)
        return SubcategoryCreateResponseSchema.model_validate(subcategory_instance)

    async def update_subcategory(
            self, subcategory_id: int, data: SubcategoryUpdateSchema
    ) -> SubcategoryCreateResponseSchema:
        result = await self.__session.execute(
            select(Subcategory).where(Subcategory.id == subcategory_id)
        )
        subcategory = result.scalar_one_or_none()
        if not subcategory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subcategory not found",
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(subcategory, field, value)

        self.__session.add(subcategory)
        await self.__session.commit()
        await self.__session.refresh(subcategory)
        return SubcategoryCreateResponseSchema.model_validate(subcategory)

    async def delete_subcategory(self, subcategory_id: int) -> None:
        result = await self.__session.execute(
            select(Subcategory).where(Subcategory.id == subcategory_id)
        )
        subcategory = result.scalar_one_or_none()
        if not subcategory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subcategory not found",
            )

        await self.__session.delete(subcategory)
        await self.__session.commit()
