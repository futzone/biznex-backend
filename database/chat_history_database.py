import asyncpg
from datetime import datetime
from typing import List, Optional
from database.connection_string import connection_string
from models.chat_history_model import ChatHistoryModel


class ChatHistoryDB:
    def __init__(self):
        self.connection_string = connection_string()

    async def create_message(self, message: ChatHistoryModel) -> Optional[int]:
        conn = None
        try:
            conn = await asyncpg.connect(self.connection_string)
            query = """
            INSERT INTO chat_history (user_id, message, is_bot, timestamp)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            RETURNING id;
            """
            return await conn.fetchval(query, message.user_id, message.message, message.is_bot)
        except Exception as error:
            print(f"Error while inserting message: {error}")
            return None
        finally:
            if conn:
                await conn.close()

    async def update_message(self, message_id: int, message: ChatHistoryModel) -> bool:
        conn = None
        try:
            conn = await asyncpg.connect(self.connection_string)
            query = """
            UPDATE chat_history
            SET message = $1, is_bot = $2, timestamp = CURRENT_TIMESTAMP
            WHERE id = $3 AND user_id = $4;
            """
            result = await conn.execute(query, message.message, message.is_bot, message_id, message.user_id)
            return result == "UPDATE 1"
        except Exception as error:
            print(f"Error while updating message: {error}")
            return False
        finally:
            if conn:
                await conn.close()

    async def delete_message(self, message_id: int) -> bool:
        conn = None
        try:
            conn = await asyncpg.connect(self.connection_string)
            query = "DELETE FROM chat_history WHERE id = $1;"
            result = await conn.execute(query, message_id)
            return result == "DELETE 1"
        except Exception as error:
            print(f"Error while deleting message: {error}")
            return False
        finally:
            if conn:
                await conn.close()

    async def get_message(self, message_id: int) -> Optional[ChatHistoryModel]:
        conn = None
        try:
            conn = await asyncpg.connect(self.connection_string)
            query = "SELECT * FROM chat_history WHERE id = $1;"
            row = await conn.fetchrow(query, message_id)
            return ChatHistoryModel(**dict(row)) if row else None
        except Exception as error:
            print(f"Error while fetching message: {error}")
            return None
        finally:
            if conn:
                await conn.close()

    async def get_messages(self, user_id: int, limit: int, offset: int) -> List[ChatHistoryModel]:
        conn = None
        try:
            conn = await asyncpg.connect(self.connection_string)
            query = """
            SELECT * FROM chat_history
            WHERE user_id = $1
            ORDER BY timestamp DESC
            LIMIT $2 OFFSET $3;
            """
            rows = await conn.fetch(query, user_id, limit, offset)
            return [ChatHistoryModel(**dict(row)) for row in rows]
        except Exception as error:
            print(f"Error while fetching messages: {error}")
            return []
        finally:
            if conn:
                await conn.close()
