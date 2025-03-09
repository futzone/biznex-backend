from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from datetime import datetime, timezone

from app.api.models.user import User, UserDB
from app.api.schemas.user import Sendticket
from app.api.utils.user import AuthUtils
from app.core.databases.postgres import get_general_session


class UserRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.db = session

    async def get_all_users(self, skip: int = 0, limit: int = 100):
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    async def create_user(
        self, full_name: str, phone_number: str, password: str, permission_id: int
    ):
        try:
            hashed_password = await AuthUtils.get_password_hash(password)
            user = User(
                full_name=full_name,
                phone_number=phone_number,
                password=hashed_password,
                permission_id=permission_id,
                is_active=False,
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("User with this phone number already exists")

    async def authenticate_user(self, phone_number: str, password: str):
        result = await self.db.execute(
            select(User).filter(User.phone_number == phone_number)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        is_valid = await AuthUtils.verify_password(password, user.password)
        if not is_valid:
            return None

        return user

    async def get_user_by_id(self, user_id: int):
        result = await self.db.execute(select(User).filter(User.id == int(user_id)))
        return result.scalar_one_or_none()

    async def update_user(self, user: User):
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int):
        user = await self.get_user_by_id(user_id)
        if user:
            await self.db.delete(user)
            await self.db.commit()
            return True
        return False

    async def send_ticket(self, data: Sendticket):
        user = UserDB(name=data.name, email=data.email)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
