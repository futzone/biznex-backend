import os
import logging
import google.generativeai as genai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from app.api.models.user import ChatHistory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def configure_gemini():
    api_key = "AIzaSyAIqcIv26rRI2sLfwL9n8MiMjSz6NMXHsg"
    # logger.info(f"Configuring Gemini with API key: {api_key[:5]}...")
    genai.configure(api_key=api_key)

async def load_history(session: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
    try:
        result = await session.execute(
            select(ChatHistory)
            .where(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.timestamp.asc())
        )
        
        history = []
        for chat in result.scalars().all():
            role = "user" if not chat.is_bot else "model"
            # Clean data from database
            cleaned_message = chat.message.replace('\n', ' ').strip()
            history.append({
                "role": role,
                "parts": [{"text": cleaned_message}]
            })
        
        # logger.info(f"Loaded {len(history)} messages from history for user {user_id}")
        return history
    except Exception as e:
        logger.error(f"Error loading history: {str(e)}")
        return [
            {"role": "user", "parts": [{"text": "Salom"}]},
            {"role": "model", "parts": [{"text": "Assalomu alaykum!"}]}
        ]

def get_chat_session(history):
    try:
        configure_gemini()
        
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        
        # logger.info("Creating Gemini model...")
        model = genai.GenerativeModel(
            model_name="tunedModels/zamonaierpchat-erygvkht87tn",
            generation_config=generation_config,
        )
        
        # logger.info(f"Starting chat with {len(history)} history items")
        return model.start_chat(history=history)
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        # Fallback to using a standard model if tuned model fails
        try:
            logger.info("Falling back to gemini-pro model...")
            model = genai.GenerativeModel(
                model_name="tunedModels/zamonaierpchat-erygvkht87tn",
                generation_config=generation_config,
            )
            return model.start_chat(history=history)
        except Exception as fallback_error:
            # logger.error(f"Fallback also failed: {str(fallback_error)}")
            raise