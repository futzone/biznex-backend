import os
import uuid
from typing import List, Sequence, Optional
from fastapi import APIRouter, Depends, status, HTTPException, File, UploadFile, Form
from pydantic import ValidationError

from app.api.controllers.product.rating import RatingController
from app.api.schemas.product.rating import (
    ProductRatingStatsResponse,
    RatingCreateSchema,
    RatingUpdateSchema,
    RatingResponseSchema,
)
from app.api.utils.user import AuthUtils

router = APIRouter()


@router.get(
    "/", response_model=Sequence[RatingResponseSchema], status_code=status.HTTP_200_OK
)
async def get_ratings(
    controller: RatingController = Depends(),
) -> Sequence[RatingResponseSchema]:
    return await controller.get_ratings()


@router.get(
    "/{rating_id}/", response_model=RatingResponseSchema, status_code=status.HTTP_200_OK
)
async def get_rating(
    rating_id: int, controller: RatingController = Depends()
) -> RatingResponseSchema:
    return await controller.get_rating_by_id(rating_id)

@router.get("/rating/{product_id}/stats", response_model=ProductRatingStatsResponse, status_code=status.HTTP_200_OK)
async def get_product_rating_stats(
    product_id: int,
    controller: RatingController = Depends()
) -> ProductRatingStatsResponse:
    
    return await controller.get_product_rating_stats(product_id)

@router.post(
    "/", response_model=RatingResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_rating(
    rating: int = Form(..., ge=1, le=5),
    comment: str = Form(...),
    current_user: dict = Depends(AuthUtils.get_current_user_from_cookie),
    product_id: int = Form(...),
    pictures: List[str] = Form(None),
    controller: RatingController = Depends(),
) -> RatingResponseSchema:


    try:
        data = RatingCreateSchema(
            rating=rating,
            comment=comment,
            user_id=str(current_user.get("sub")),
            product_id=product_id,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    return await controller.create_rating(data, pictures)


@router.put(
    "/{rating_id}/", response_model=RatingResponseSchema, status_code=status.HTTP_200_OK
)
async def partial_update_rating(
    rating_id: int,
    rating: Optional[int] = Form(None, ge=1, le=5),
    comment: Optional[str] = Form(None),
    pictures: List[str] = Form(None),
    controller: RatingController = Depends(),
) -> RatingResponseSchema:

    old_rating = await controller.get_rating_by_id(rating_id)
    if not old_rating:
        raise HTTPException(status_code=404, detail="Rating not found for update")

    final_rating = rating if rating is not None else old_rating.rating
    final_comment = comment if comment is not None else old_rating.comment

    try:
        data = RatingUpdateSchema(rating=final_rating, comment=final_comment)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    new_picture_paths: List[str] = []
    if pictures:
        for old_pic in old_rating.pictures:
            if old_pic.image_path and os.path.isfile(old_pic.image_path):
                try:
                    os.remove(old_pic.image_path)
                except OSError:
                    pass

        

    return await controller.update_rating(rating_id, data, pictures)


@router.delete("/{rating_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rating(
    rating_id: int, controller: RatingController = Depends()
) -> None:
    old_rating = await controller.get_rating_by_id(rating_id)
    if not old_rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found",
        )
    for pic in old_rating.pictures:
        if pic.image_path and os.path.isfile(pic.image_path):
            try:
                os.remove(pic.image_path)
            except OSError:
                pass

    await controller.delete_rating(rating_id)
    return None
