from typing import List, Optional
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.databases.postgres import get_general_session
from app.api.models.product import ProductImage
from app.api.schemas.product.product_image import (
    ProductImageCreateSchema,
    ProductImageUpdateSchema,
    ProductImageResponseSchema,
)


class ProductImageRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def get_images(self) -> List[ProductImageResponseSchema]:
        result = await self.__session.execute(select(ProductImage))
        imgs = result.scalars().all()
        return [ProductImageResponseSchema.model_validate(i) for i in imgs]

    async def get_image_by_id(
            self, image_id: int
    ) -> Optional[ProductImageResponseSchema]:
        result = await self.__session.execute(
            select(ProductImage).where(ProductImage.id == image_id)
        )
        i = result.scalar_one_or_none()
        if not i:
            return None
        return ProductImageResponseSchema.model_validate(i)

    async def create_image(
            self, data: ProductImageCreateSchema
    ) -> ProductImageResponseSchema:
        img_obj = ProductImage(**data.model_dump())
        self.__session.add(img_obj)
        await self.__session.commit()
        await self.__session.refresh(img_obj)
        return ProductImageResponseSchema.model_validate(img_obj)

    async def update_image(
            self, image_id: int, data: ProductImageUpdateSchema
    ) -> ProductImageResponseSchema:
        result = await self.__session.execute(
            select(ProductImage).where(ProductImage.id == image_id)
        )
        i = result.scalar_one_or_none()
        if not i:
            raise HTTPException(404, "ProductImage not found")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(i, field, value)
        self.__session.add(i)
        await self.__session.commit()
        await self.__session.refresh(i)
        return ProductImageResponseSchema.model_validate(i)

    async def delete_image(self, image_id: str, variant_id) -> None:
        result = await self.__session.execute(
            select(ProductImage).where(ProductImage.image == image_id, ProductImage.product_variant_id == variant_id)
        )
        images = result.scalars().all()
        if not images:
            raise HTTPException(404, "ProductImage not found")
        for img in images:
            await self.__session.delete(img)
        await self.__session.commit()

