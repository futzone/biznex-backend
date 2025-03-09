from typing import List
from fastapi import Depends, HTTPException

from app.api.repositories.product.product_image import ProductImageRepository
from app.api.schemas.product.product_image import (
    ProductImageCreateSchema,
    ProductImageUpdateSchema,
    ProductImageResponseSchema,
)


class ProductImageController:
    def __init__(self, repo: ProductImageRepository = Depends()):
        self.__repo = repo

    async def get_images(self) -> List[ProductImageResponseSchema]:
        return await self.__repo.get_images()

    async def get_image_by_id(self, image_id: int) -> ProductImageResponseSchema:
        i = await self.__repo.get_image_by_id(image_id)
        if not i:
            raise HTTPException(404, "Image not found")
        return i

    async def create_image(
        self, data: ProductImageCreateSchema
    ) -> ProductImageResponseSchema:
        return await self.__repo.create_image(data)

    async def update_image(
        self, image_id: int, data: ProductImageUpdateSchema
    ) -> ProductImageResponseSchema:
        return await self.__repo.update_image(image_id, data)

    async def delete_image(self, image_id: int) -> None:
        return await self.__repo.delete_image(image_id)
