from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.models.user import User
from app.core.databases.postgres import get_general_session
from fastapi import Depends


class UserRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.db = session

    async def create_user(
        self,
        full_name: str,
        phone_number: str,
        password: str,
        profile_picture: str,
    ):
        user = User(
            full_name=full_name,
            phone_number=phone_number,
            password=password,
            profile_picture=profile_picture,
            is_active=False,
        )
        self.db.add(user)
        await self.db.commit()
        return user

    async def get_user_by_phone(self, phone_number: str):
        result = await self.db.execute(
            select(User).filter(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()

    async def activate_user(self, user_id: int):
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            user.is_active = True
            await self.db.commit()
            return user

        return None

    async def get_user_by_id(self, user_id: int):
        result = await self.db.execute(select(User).filter(User.id == user_id))
        return result.scalar_one_or_none()

    async def update_user(self, user: User):
        self.db.add(user)
        await self.db.commit()
        return user
