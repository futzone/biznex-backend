from typing import List, Optional
from fastapi import Depends, HTTPException, status

from app.api.repositories.product.product import ProductRepository
from app.api.repositories.product.rating import RatingRepository
from app.api.schemas.product.rating import (
    ProductRatingStatsResponse,
    RatingCreateSchema,
    RatingUpdateSchema,
    RatingResponseSchema,
)


class RatingController:
    def __init__(self, rating_repository: RatingRepository = Depends(), product_repository: ProductRepository = Depends()):
        self.__rating_repository = rating_repository
        self.__product_repository = product_repository

    async def get_ratings(self) -> List[RatingResponseSchema]:
        return await self.__rating_repository.get_ratings()

    async def get_product_rating_stats(self, product_id: int) -> ProductRatingStatsResponse:
        product = await self.__product_repository.get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        stats = await self.__rating_repository.get_product_rating_stats(product_id)
        return stats

    async def get_rating_by_id(self, rating_id: int) -> RatingResponseSchema:
        rating = await self.__rating_repository.get_rating_by_id(rating_id)
        if not rating:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found"
            )
        return rating

    async def create_rating(
        self, data: RatingCreateSchema, picture_paths: List[str]
    ) -> RatingResponseSchema:
        return await self.__rating_repository.create_rating(data, picture_paths)

    async def update_rating(
        self, rating_id: int, data: RatingUpdateSchema, new_picture_paths: List[str]
    ) -> RatingResponseSchema:
        return await self.__rating_repository.update_rating(
            rating_id, data, new_picture_paths
        )

    async def delete_rating(self, rating_id: int) -> None:
        return await self.__rating_repository.delete_rating(rating_id)
