from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.models.user import ChatHistory
from typing import List

class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_message(self, user_id: int, message: str, is_bot: bool = False):
        try:
            chat = ChatHistory(
                user_id=user_id,
                message=message,
                is_bot=is_bot,
                timestamp=datetime.now()
            )
            self.session.add(chat)
            await self.session.commit()
            return chat
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_history(self, user_id: int, limit: int = 100) -> List[ChatHistory]:
        try:
            result = await self.session.execute(
                select(ChatHistory)
                .where(ChatHistory.user_id == user_id)
                .order_by(ChatHistory.timestamp.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            raise e