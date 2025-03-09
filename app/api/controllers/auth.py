import os
import random
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.models.user import User
from app.api.repositories.smsrepositories import SMSRepository
from app.api.repositories.auth import UserRepository
from app.api.utils.user import AuthUtils
from app.core import settings
from fastapi import status

settings = settings.get_settings()


class AuthController:
    @classmethod
    async def register_user(
        cls,
        full_name: str,
        phone_number: str,
        password: str,
        profile_picture: str,
        db: AsyncSession,
    ):
        user_repo = UserRepository(db)
        sms_repo = SMSRepository(db)

        existing_user = await user_repo.get_user_by_phone(phone_number=phone_number)
        if existing_user:
            raise HTTPException(
                status_code=400, detail="Phone number is already registered"
            )

        user = await user_repo.create_user(
            full_name=full_name,
            phone_number=phone_number,
            password=password,
            profile_picture=profile_picture,
        )

        code = str(random.randint(100000, 999999))
        expired_at = datetime.utcnow() + timedelta(minutes=10)

        await sms_repo.create_sms_code(
            user_id=user.id, code=code, expired_at=expired_at
        )
        return {
            "message": "Registration successful. Verify the OTP sent to your phone.",
            "otp": code,
        }

    @classmethod
    async def verify_sms_code(cls, phone_number: str, code: str, db: AsyncSession):
        user_repo = UserRepository(db)
        sms_repo = SMSRepository(db)

        user = await user_repo.get_user_by_phone(phone_number=phone_number)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        sms_code = await sms_repo.get_valid_sms_code(user_id=user.id, code=code)
        if not sms_code:
            raise HTTPException(status_code=400, detail="Invalid or expired SMS code")

        await sms_repo.mark_sms_as_used(sms_code.id)

        await user_repo.activate_user(user_id=user.id)

        return {"message": "SMS code verified successfully. Account is now active."}

    @classmethod
    async def login_user(
        cls, phone_number: str, password: str, db: AsyncSession, response: Response
    ):
        user_repo = UserRepository(db)
        user = await user_repo.get_user_by_phone(phone_number=phone_number)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user or user.password != password:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="Account is not verified. Please verify the OTP sent to your phone.",
            )

        access_token_expires = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        access_token = await AuthUtils.create_access_token(
            data={
                "sub": str(user.id),
                "role": str("customer"),
                "is_active": user.is_active,
                "phone_number": user.phone_number,
            },
            expired_minute=access_token_expires,
        )

        refresh_token_expires = settings.REFRESH_TOKEN_EXPIRE_DAYS
        refresh_token = await AuthUtils.create_refresh_token(
            data={"sub": str(user.id), "role": str("customer")},
            expired_days=refresh_token_expires,
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            max_age=refresh_token_expires,
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=access_token_expires,
        )

        return {
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "phone_number": user.phone_number,
            },
        }

    async def update_user(
        user_id: int,
        full_name: Optional[str] = None,
        profile_picture: Optional[str] = None,
        db: AsyncSession = None,
    ) -> User:
        user_repo = UserRepository(db)
        user = await user_repo.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if profile_picture and user.profile_picture:
            try:
                if os.path.exists(user.profile_picture):
                    os.remove(user.profile_picture)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error deleting old image: {str(e)}",
                )

        if full_name:
            user.full_name = full_name
        if profile_picture:
            user.profile_picture = profile_picture

        await user_repo.update_user(user)

        return user

    @classmethod
    async def refresh_token(cls, refresh_token: bytes, response: JSONResponse):
        try:

            payload = jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id = payload.get("sub")
            role = payload.get("role")

            if not isinstance(payload.get("sub"), str):
                raise HTTPException(
                    status_code=400,
                    detail="Subject must be a string"
                    )

            if user_id is None:
                raise HTTPException(status_code=403, detail="Invalid refresh token")

            access_token_expires = settings.ACCESS_TOKEN_EXPIRE_MINUTES
            access_token = await AuthUtils.create_access_token(
                data={"sub": str(user_id), "role": str(role)},
                expired_minute=access_token_expires,
            )

            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                max_age=access_token_expires,
            )

            return {"access_token": access_token}

        except HTTPException as e:
            raise HTTPException(status_code=500, detail=f"Internal server error {e}")

    @classmethod
    async def verify_reset_code(
        cls,
        phone_number: str,
        code: str,
        db: AsyncSession,
    ):
        user_repo = UserRepository(db)
        sms_repo = SMSRepository(db)

        user = await user_repo.get_user_by_phone(phone_number=phone_number)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        sms_code = await sms_repo.get_valid_sms_code(user_id=user.id, code=code)
        if not sms_code:
            raise HTTPException(status_code=400, detail="Invalid or expired SMS code")

        await sms_repo.mark_sms_as_used(sms_code.id)

        reset_token = await AuthUtils.create_access_token(
            data={
                "sub": str(user.id),
                "type": "password_reset",
                "phone_number": phone_number,
            },
            expired_minute=15,
        )

        return {"message": "Code verified successfully", "reset_token": reset_token}

    @classmethod
    async def update_password(
        cls,
        old_password: str,
        new_password: str,
        current_user: User,
        db: AsyncSession,
    ):
        user_repo = UserRepository(db)

        if current_user.password != old_password:
            raise HTTPException(status_code=400, detail="Eski parol noto'g'ri")

        hashed_password = await AuthUtils.get_password_hash(new_password)
        current_user.password = hashed_password
        await user_repo.update_user(current_user)

        return {"message": "Parol muvaffaqiyatli yangilandi"}

    @classmethod
    async def logout_user(cls, response: Response):

        response.delete_cookie(key="access_token")

        return {"message": "Logout successful"}

    @classmethod
    async def forgot_password(
        cls, phone_number: str, db: AsyncSession, response: Response
    ):
        user_repo = UserRepository(db)
        sms_repo = SMSRepository(db)

        user = await user_repo.get_user_by_phone(phone_number=phone_number)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        code = str(random.randint(100000, 999999))
        expired_at = datetime.utcnow() + timedelta(minutes=10)

        await sms_repo.create_sms_code(
            user_id=user.id, code=code, expired_at=expired_at
        )

        print(f"Generated SMS Code for user {user.id}: {code}") 

        return {
            "message": "A verification code has been sent to your phone.",
            "code": code,
        }

    @classmethod
    async def reset_password(
        cls,
        reset_token: str,
        new_password: str,
        response: Response,
        db: AsyncSession,
    ):
        user_repo = UserRepository(db)

        try:
            payload = await AuthUtils.verify_token(
                token=reset_token,
            )

            if payload.get("type") != "password_reset":
                raise HTTPException(status_code=400, detail="Invalid reset token")

            user_id = payload.get("sub")
            phone_number = payload.get("phone_number")

            user = await user_repo.get_user_by_phone(phone_number=phone_number)
            if not user or str(user.id) != user_id:
                raise HTTPException(status_code=404, detail="User not found")

            hashed_password = await AuthUtils.get_password_hash(new_password)

            user.password = hashed_password
            await user_repo.update_user(user)

            expired_token = await AuthUtils.create_access_token(
                data={"sub": user_id},
                expired_minute=-1,
            )

            response.set_cookie(
                key="access_token", value=expired_token, httponly=True, max_age=0
            )

            return {"message": "Password has been successfully reset"}

        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid or expired reset token {e}"
            )

    @classmethod
    async def get_current_user(
        self,
        request: Request,
        session: AsyncSession,
    ):
        user_repo = UserRepository(session=session)
        token = await AuthUtils.get_current_user_from_cookie(request)
        if not token:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user = await user_repo.get_user_by_id(int(token["sub"]))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user
