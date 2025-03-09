from typing import Optional, Sequence, List
from fastapi import Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload

from app.core.databases.postgres import get_general_session
from app.api.models.product import Rating, RatingPicture
from app.api.schemas.product.rating import (
    ProductRatingStatsResponse,
    RatingCreateSchema,
    RatingResponseSchema,
    RatingUpdateSchema,
    ReviewSampleResponse,
)


class RatingRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def get_ratings(self) -> List[RatingResponseSchema]:
        result = await self.__session.execute(
            select(Rating).options(joinedload(Rating.pictures))
        )

        ratings = result.unique().scalars().all()

        return [RatingResponseSchema.model_validate(r) for r in ratings]

    async def get_product_rating_stats(self, product_id: int) -> ProductRatingStatsResponse:
        rating_counts_query = select(
            Rating.rating,
            func.count(Rating.id).label("count")
        ).where(
            Rating.product_id == product_id
        ).group_by(
            Rating.rating
        )
        
        rating_counts_result = await self.__session.execute(rating_counts_query)
        rating_counts = {row.rating: row.count for row in rating_counts_result}
        
        rating_distribution = {
            1: rating_counts.get(1, 0),
            2: rating_counts.get(2, 0),
            3: rating_counts.get(3, 0),
            4: rating_counts.get(4, 0),
            5: rating_counts.get(5, 0)
        }
        
        total_ratings = sum(rating_distribution.values())
        
        if total_ratings > 0:
            weighted_sum = sum(rating * count for rating, count in rating_distribution.items())
            average_rating = round(weighted_sum / total_ratings, 1)
            percentage_score = int(round((average_rating / 5) * 100))
        else:
            average_rating = 0.0
            percentage_score = 0
        
        sample_reviews_query = select(
            Rating
        ).where(
            Rating.product_id == product_id
        ).options(
            selectinload(Rating.pictures),
            selectinload(Rating.user)
        ).order_by(
            Rating.created_at.desc()
        ).limit(3)
        
        sample_reviews_result = await self.__session.execute(sample_reviews_query)
        sample_reviews = sample_reviews_result.scalars().all()
        
        sample_reviews_response = []
        for review in sample_reviews:
            user_name = review.user.full_name if review.user else "Anonymous"
            sample_reviews_response.append(
                ReviewSampleResponse(
                    user_name=user_name,
                    user_avatar=review.user.profile_picture if review.user else None,
                    rating=review.rating,
                    comment=review.comment,
                    images=[pic.image_path for pic in review.pictures] if review.pictures else []
                )
            )
        
        return ProductRatingStatsResponse(
            average_rating=average_rating,
            total_ratings=total_ratings,
            rating_distribution=rating_distribution,
            percentage_score=percentage_score,
            sample_reviews=sample_reviews_response
        )

    async def get_rating_by_id(self, rating_id: int) -> Optional[RatingResponseSchema]:

        result = await self.__session.execute(
            select(Rating)
            .where(Rating.id == rating_id)
            .options(joinedload(Rating.pictures))
        )
        rating_obj = result.unique().scalars().first()
        if not rating_obj:
            return None
        return RatingResponseSchema.model_validate(rating_obj)

    async def create_rating(
        self, data: RatingCreateSchema, picture_paths: List[str]
    ) -> RatingResponseSchema:
        rating_instance = Rating(
            rating=data.rating,
            comment=data.comment,
            user_id=data.user_id,
            product_id=data.product_id,
        )
        self.__session.add(rating_instance)
        await self.__session.commit()
        await self.__session.refresh(rating_instance)

        for path in picture_paths:
            pic = RatingPicture(rating_id=rating_instance.id, image_path=path)
            self.__session.add(pic)
        await self.__session.commit()

        result = await self.__session.execute(
            select(Rating)
            .where(Rating.id == rating_instance.id)
            .options(joinedload(Rating.pictures))
        )
        rating_with_pics = result.unique().scalar_one()

        return RatingResponseSchema.model_validate(rating_with_pics)

    async def update_rating(
        self,
        rating_id: int,
        data: RatingUpdateSchema,
        new_picture_paths: List[str],
    ) -> RatingResponseSchema:
        result = await self.__session.execute(
            select(Rating)
            .where(Rating.id == rating_id)
            .options(joinedload(Rating.pictures))
        )
        rating_obj = result.unique().scalars().first()
        if not rating_obj:
            raise HTTPException(404, "Rating not found")

        rating_obj.rating = data.rating
        rating_obj.comment = data.comment

        self.__session.add(rating_obj)
        await self.__session.commit()
        await self.__session.refresh(rating_obj)

        if new_picture_paths:
            for old_pic in rating_obj.pictures:
                await self.__session.delete(old_pic)
            await self.__session.commit()

            for path in new_picture_paths:
                pic = RatingPicture(rating_id=rating_obj.id, image_path=path)
                self.__session.add(pic)
            await self.__session.commit()

        result2 = await self.__session.execute(
            select(Rating)
            .where(Rating.id == rating_obj.id)
            .options(joinedload(Rating.pictures))
        )
        final_obj = result2.unique().scalars().one()

        return RatingResponseSchema.model_validate(final_obj)

    async def delete_rating(self, rating_id: int) -> None:
        result = await self.__session.execute(
            select(Rating)
            .where(Rating.id == rating_id)
            .options(joinedload(Rating.pictures))
        )
        rating_obj = result.unique().scalars().first()
        if not rating_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rating not found",
            )

        await self.__session.delete(rating_obj)
        await self.__session.commit()
