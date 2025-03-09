from datetime import datetime, timedelta
import random
from fastapi import Depends, HTTPException, status
from app.api.models.user import SMSCode, User
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.databases.postgres import get_general_session


class SMSCodeService:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.db = session

    async def create_sms_code(self, user_id: int):
        code = random.randint(100000, 999999)
        expired_at = datetime.utcnow() + timedelta(minutes=2)
        sms_code = SMSCode(user_id=user_id, code=code, expired_at=expired_at)

        self.db.add(sms_code)
        await self.db.commit()
        await self.db.refresh(sms_code)

        print(f"Generated SMS code for user {user_id}: {code}")
        return sms_code

    async def verify_sms_code(self, user_id: int, code: int):
        from sqlalchemy import select

        result = await self.db.execute(
            select(SMSCode)
            .where(SMSCode.user_id == user_id)
            .order_by(SMSCode.created_at.desc())
            .limit(1)
        )
        sms_code = result.scalar_one_or_none()
        if (
            sms_code
            and sms_code.code == code
            and sms_code.expired_at > datetime.utcnow()
        ):
            return True
        return False

    async def resend_sms_code(self, user_id: int):
        return await self.create_sms_code(user_id)


def get_sms_service(
    session: AsyncSession = Depends(get_general_session),
) -> SMSCodeService:
    return SMSCodeService(session=session)
