import datetime
import logging
from fastapi import APIRouter, HTTPException
from app.api.controllers.chat import ChatController
from app.api.repositories.chat import ChatRepository
from app.core.databases.postgres import get_general_session
from typing import List

from database.chat_history_database import ChatHistoryDB
from models.chat_history_model import ChatMessage
from utils.message_generator import generate_response

logger = logging.getLogger(__name__)
from models.chat_history_model import ChatHistoryModel

router = APIRouter()


@router.get("/history/{user_id}", response_model=List[ChatHistoryModel])
async def get_chat_history(user_id: int, limit: int = 100):
    history_db = ChatHistoryDB()
    chat_history = await history_db.get_messages(user_id=user_id, limit=limit, offset=0)

    return chat_history


@router.post("/history/{user_id}", response_model=List[ChatHistoryModel])
async def send_message(user_id: int, message: ChatMessage):
    history_db = ChatHistoryDB()
    chat_message = ChatHistoryModel(
        user_id=user_id, message=message.message,
        is_bot=False, timestamp=datetime.datetime.utcnow()
    )
    await history_db.create_message(message=chat_message)
    message_reply = generate_response(message.message)
    chat_message_bot = ChatHistoryModel(
        user_id=user_id, message=message_reply,
        is_bot=True, timestamp=datetime.datetime.utcnow()
    )
    await history_db.create_message(message=chat_message_bot)

    chat_history = await history_db.get_messages(user_id=user_id, limit=100, offset=0)

    return chat_history
