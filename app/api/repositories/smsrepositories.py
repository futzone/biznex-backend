from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from app.api.models import SMSCode
from utils.time_utils import now_time


class SMSRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def create_sms_code(self, user_id: int, code: str, expired_at: datetime):
        sms_code = SMSCode(
            user_id=user_id,
            code=code,
            created_at=now_time(),
            expired_at=expired_at,
            is_used=False,
        )
        self.db.add(sms_code)
        await self.db.commit()
        return sms_code

    async def get_valid_sms_code(self, user_id: int, code: str):
        result = await self.db.execute(
            select(SMSCode).filter(
                and_(
                    SMSCode.user_id == user_id,
                    SMSCode.code == code,
                    SMSCode.is_used == False,
                    SMSCode.expired_at > now_time(),
                )
            )
        )
        return result.scalar_one_or_none()

    async def mark_sms_as_used(self, sms_code_id: int):
        result = await self.db.execute(
            select(SMSCode).filter(SMSCode.id == sms_code_id)
        )
        sms_code = result.scalar_one_or_none()

        if sms_code:
            sms_code.is_used = True
            await self.db.commit()
            return sms_code

        return None
