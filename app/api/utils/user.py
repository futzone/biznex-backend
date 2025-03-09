import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.api.models.user import AdminUser
from app.api.repositories.admin import AdminRepository
from app.core.databases.postgres import get_general_session
from app.core.settings import Settings
from sqlalchemy.ext.asyncio import AsyncSession

settings = Settings()
admin_repo = AdminRepository()


class AuthUtils:
    @classmethod
    async def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    @classmethod
    async def get_password_hash(cls, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @classmethod
    async def create_access_token(cls, data: dict, expired_minute: int = 1440) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + \
            (timedelta(minutes=expired_minute))
        to_encode.update({"exp": expire.timestamp()})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @classmethod
    async def create_refresh_token(cls, data: dict, expired_days: int) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (timedelta(days=expired_days))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    async def get_current_user_from_token(
        token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")),
    ) -> dict:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=settings.ALGORITHM
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=401, detail="Could not validate credentials"
            )

    @staticmethod
    async def verify_token(
        token: str,
    ) -> dict:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=settings.ALGORITHM
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=401, detail="Could not validate credentials"
            )

    @staticmethod
    async def get_current_user_from_cookie(request: Request) -> dict:
        access_token = request.headers.get("Authorization")
        if not access_token:
            access_token = request.cookies.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=401, detail="Access token not found")

        try:
            payload = jwt.decode(
                access_token, settings.SECRET_KEY, algorithms=settings.ALGORITHM
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=401, detail="Could not validate credentials {e}"
            )

    # @staticmethod
    # async def get_user_info_from_token(request: Request):
    #     access_token = request.cookies.get("access_token")
    #     if not access_token:
    #         raise HTTPException(status_code=401, detail="Access token not found")

    #     try:
    #         payload = jwt.decode(
    #             access_token, settings.SECRET_KEY, algorithms=settings.ALGORITHM
    #         )

    #         user = await admin_repo.get_user_by_id(payload["sub"])
    #         return user

    #     except JWTError:
    #         raise HTTPException(
    #             status_code=401, detail="Could not validate credentials"
    #         )
    @classmethod
    async def expire_token(cls, token: str) -> str:
        try:
            # Tokenni dekodlash va payloadni olish
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )

            # Muddati tugagan deb belgilash
            expired_token = payload.copy()
            expired_token["exp"] = datetime.now(timezone.utc)  # Muddati tugadi

            # Yangi expired tokenni qaytarish
            expired_token_str = jwt.encode(
                expired_token, settings.SECRET_KEY, algorithm=settings.ALGORITHM
            )
            return expired_token_str
        except jwt.JWTError:
            raise HTTPException(
                status_code=401, detail=f"Could not validate credentials"
            )

    @classmethod
    async def get_current_admin_user(
        cls,
        request: Request,
        session: AsyncSession = Depends(get_general_session),
    ) -> AdminUser:
        try:
            payload = await cls.get_current_user_from_cookie(request)

            admin_id = int(payload["sub"])
            admin = await session.get(AdminUser, admin_id)
            if not admin:
                raise HTTPException(status_code=404, detail="Admin not found")

            return admin
        except JWTError:
            raise HTTPException(
                status_code=401, detail="Could not validate credentials"
            )
