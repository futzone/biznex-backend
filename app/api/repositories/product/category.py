from typing import Optional, Sequence, Any, Coroutine, List
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.databases.postgres import get_general_session
from app.api.models.product import Category, Subcategory
from app.api.schemas.product.category import (
    CategoryCreateSchema,
    CategoryUpdateSchema,
    CategoryResponseSchema,
    CategoryCreateResponseSchema,
)


class CategoryRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def get_warehouse_categories(self, warehouse_id, language):

        result = await self.__session.execute(
            select(Category)
            .options(
                selectinload(Category.subcategories).selectinload(Subcategory.products)
            ).where(Category.warehouse_id == warehouse_id)
        )
        categories = result.scalars().all()
        categories_with_product = []

        for category in categories:
            product_count = sum(len(subcategory.products)for subcategory in category.subcategories)
            categories_with_product.append(
                CategoryResponseSchema(
                    id=category.id,
                    name=category.name.get(language, ""),
                    image=category.image,
                    description=category.description.get(language, ""),
                    product_count=product_count
                )
            )

        return categories_with_product
    
    async def get_categories(self, language):
        result = await self.__session.execute(
            select(Category)
            .options(
                selectinload(Category.subcategories).selectinload(Subcategory.products)
            )
        )
        categories = result.scalars().all()
        categories_with_product = []

        for category in categories:
            product_count = sum(len(subcategory.products)for subcategory in category.subcategories)
            categories_with_product.append(
                CategoryResponseSchema(
                    id=category.id,
                    name=category.name.get(language, ""),
                    image=category.image,
                    description=category.description.get(language, ""),
                    product_count=product_count
                )
            )

        return categories_with_product

    async def get_warehouse_category_by_id(
        self,
        warehouse_id: int,
        category_id: int,
        language: str,
    ) -> Optional[CategoryResponseSchema] | CategoryCreateResponseSchema:
        result = await self.__session.execute(
            select(Category).where(
                Category.warehouse_id == warehouse_id,
                Category.id == category_id,
            )
        )
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        if language is not None:
            return CategoryResponseSchema(
                id=category.id,
                name=category.name.get(language, ""),
                image=category.image,
                description=(
                    category.description.get(language, "")
                    if category.description
                    else None
                ),
            )
        return CategoryCreateResponseSchema.model_validate(category)
    
    async def get_category_by_id(self, category_id, language):
        result = await self.__session.execute(
            select(Category).where(
                Category.id == category_id,
            )
        )
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        if language is not None:
            return CategoryResponseSchema(
                id=category.id,
                name=category.name.get(language, ""),
                image=category.image,
                description=(
                    category.description.get(language, "")
                    if category.description
                    else None
                ),
            )
        return CategoryCreateResponseSchema.model_validate(category)

    async def create_category(
        self, warehouse_id, translated_name, translated_description, image
    ) -> CategoryCreateResponseSchema:

        data = {
            "warehouse_id": warehouse_id,
            "name": translated_name,
            "image": image,
            "description": translated_description,
        }

        category_instance = Category(**data)
        self.__session.add(category_instance)
        await self.__session.commit()
        await self.__session.refresh(category_instance)
        return CategoryCreateResponseSchema.model_validate(category_instance)

    async def update_category(
        self, category_id: int, data: CategoryUpdateSchema
    ) -> CategoryCreateResponseSchema:
        result = await self.__session.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)

        self.__session.add(category)
        await self.__session.commit()
        await self.__session.refresh(category)
        return CategoryCreateResponseSchema.model_validate(category)

    async def delete_category(self, category_id: int) -> None:
        result = await self.__session.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        await self.__session.delete(category)
        await self.__session.commit()
