from pydantic import BaseModel
from datetime import datetime


class ChatMessage(BaseModel):
    message: str


class ChatHistoryModel(BaseModel):
    id: int | None = None
    user_id: int
    message: str
    is_bot: bool
    timestamp: datetime

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "id": self.id,
            "message": self.message,
            "is_bot": self.is_bot,
            "timestamp": f"{self.timestamp}"
        }
