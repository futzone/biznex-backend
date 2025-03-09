from typing import List
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.user import AuthUtils
from app.core.databases.postgres import get_general_session
from app.api.schemas.user import User, UserCreate, UserUpdate
from app.api.repositories.user import UserRepository
from app.api.utils.sendform import send_form


class UserController:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__user_repository = UserRepository(session)

    async def get_current_user(
        self, token: str = Depends(AuthUtils.get_current_user_from_token)
    ) -> User:
        if not token:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        user = await self.__user_repository.get_user_by_id(token["sub"])
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return await self.__user_repository.get_all_users(skip, limit)

    async def get_user_by_id(self, user_id: int) -> User:
        user = await self.__user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
        return user

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        existing_user = await self.__user_repository.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
        return await self.__user_repository.update_user(user_id, user_data)

    async def delete_user(self, user_id: int):
        existing_user = await self.__user_repository.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
        await self.__user_repository.delete_user(user_id)


    async def send_ticket(self, data):
        return await self.__user_repository.send_ticket(data)

    async def send_form(self, data):
        return send_form(data)