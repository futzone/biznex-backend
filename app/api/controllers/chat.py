from datetime import datetime
import logging
from typing import List, Dict, Any
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.repositories.chat import ChatRepository
from app.api.schemas.chat_schema import ChatResponse, ChatHistoryResponse
from app.core.gemini import load_history, get_chat_session

logger = logging.getLogger(__name__)

class ChatController:
    def __init__(self, repository: ChatRepository):
        self.repository = repository

    async def process_message(self, user_id: int, message: str, session: AsyncSession) -> ChatResponse:
        try:
            logger.info(f"Processing message for user {user_id}: {message[:20]}...")
            
            await self.repository.save_message(user_id, message, is_bot=False)
            
            chat_session = await self._get_chat_session(user_id, session)
            
            logger.info("Sending message to Gemini...")
            try:
                response = chat_session.send_message(message)
                
                if not response.text:
                    raise ValueError("AI did not provide a response")
                
                logger.info(f"Received response from Gemini: {response.text[:20]}...")
            except Exception as e:
                logger.error(f"Error in send_message: {str(e)}")
                if hasattr(e, 'details'):
                    logger.error(f"Error details: {e.details}")
                raise e
            
            await self.repository.save_message(user_id, response.text, is_bot=True)
            
            response_dict = {
                "message": response.text,
                "user_id": user_id,
                "is_bot": True
            }
            
            return ChatResponse(**response_dict)
        except Exception as e:
            error_message = f"Error processing message: {str(e)}"
            logger.error(error_message)
            
            await self.repository.save_message(user_id, f"Xatolik: {str(e)}", is_bot=True)
            
            raise Exception(error_message)

    async def _get_chat_session(self, user_id: int, session: AsyncSession):
        try:
            history = await load_history(session, user_id)
            
            return get_chat_session(history)
        except Exception as e:
            logger.error(f"Error in _get_chat_session: {str(e)}")
            raise e
    
    async def get_chat_history(self, user_id: int, limit: int = 100) -> List[ChatHistoryResponse]:
        try:
            history = await self.repository.get_history(user_id, limit)
            
            responses = []
            for item in history:
                responses.append(ChatHistoryResponse(
                    id=item.id,
                    user_id=item.user_id,
                    message=item.message,
                    is_bot=item.is_bot,
                    timestamp_str=item.timestamp.isoformat()
                ))
            
            return responses
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            raise e