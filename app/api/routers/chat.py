import json
import logging
from socketio import AsyncServer
from fastapi import APIRouter, Depends, HTTPException
from app.api.controllers.chat import ChatController
from app.api.repositories.chat import ChatRepository
from app.api.schemas.chat_schema import ChatMessage, ChatHistoryResponse
from app.core.databases.postgres import get_general_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/history/{user_id}", response_model=List[ChatHistoryResponse])
async def get_chat_history(user_id: int, limit: int = 100):
    async for session in get_general_session():
        try:
            repo = ChatRepository(session)
            controller = ChatController(repo)
            history = await controller.get_chat_history(user_id, limit)
            return history
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            await session.close()

async def register_chat_handlers(sio: AsyncServer, router: APIRouter):
    
    @sio.on('connect')
    async def connect(sid, environ):
        logger.info(f"Client connected: {sid}")

    @sio.on('disconnect')
    async def disconnect(sid):
        logger.info(f"Client disconnected: {sid}")

    @sio.on('message')
    async def handle_message(sid, data):
        logger.info(f"Received message from {sid}: {data}")

        try:
            # Parse data if it's a string
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error: {str(e)}")
                    await sio.emit("error", {"error": "JSON format noto'g'ri!"}, to=sid)
                    return
            
            if not isinstance(data, dict):
                logger.error(f"Invalid data format: {type(data)}")
                await sio.emit("error", {"error": "Noto'g'ri format: JSON obyekt kutilgan edi!"}, to=sid)
                return
            
            # Process message
            async for session in get_general_session():
                try:
                    repo = ChatRepository(session)
                    controller = ChatController(repo)
                    
                    logger.info(f"Processing message data: {data}")
                    message_data = ChatMessage(**data)
                    logger.info(f"Validated message data: {message_data.dict()}")
                    
                    response = await controller.process_message(
                        user_id=message_data.user_id,
                        message=message_data.message,
                        session=session
                    )
                    
                    logger.info(f"Sending response to {sid}")
                    await sio.emit('chat_response', response.dict(), to=sid)
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    await sio.emit('error', {'error': str(e)}, to=sid)
                finally:
                    await session.close()
        except Exception as e:
            logger.error(f"Unhandled error: {str(e)}")
            await sio.emit("error", {"error": str(e)}, to=sid)

    return router