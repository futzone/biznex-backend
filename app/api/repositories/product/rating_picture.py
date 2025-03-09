import os

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.databases.postgres import get_general_session
from app.api.models.product import RatingPicture


class RatingPictureRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def get_picture_model_by_id(self, pic_id: int) -> RatingPicture:
        result = await self.__session.execute(
            select(RatingPicture).where(RatingPicture.id == pic_id)
        )
        pic = result.scalar_one_or_none()
        if not pic:
            raise HTTPException(status_code=404, detail="Picture not found")
        return pic

    async def delete_picture(self, pic_id: int) -> None:
        pic_model = await self.get_picture_model_by_id(pic_id)
        if os.path.isfile(pic_model.image_path):
            os.remove(pic_model.image_path)

        await self.__session.delete(pic_model)
        await self.__session.commit()
