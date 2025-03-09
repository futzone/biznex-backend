from fastapi import APIRouter, Depends, status, UploadFile, File
from app.api.repositories.product.rating_picture import RatingPictureRepository

router = APIRouter()


@router.delete("/{picture_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rating_picture(
    picture_id: int, repo: RatingPictureRepository = Depends()
):
    await repo.delete_picture(picture_id)
    return
