from pydantic import BaseModel
from typing import Optional, List


class ChatMessage(BaseModel):
    user_id: int
    message: str


class ChatResponse(BaseModel):
    message: str
    user_id: int
    is_bot: bool
    timestamp_str: Optional[str] = None

    class Config:
        json_encoders = {
            # Convert datetime objects to ISO format strings
            'timestamp': lambda v: v.isoformat() if v else None
        }

    def dict(self, *args, **kwargs):
        # Override dict method to avoid datetime serialization issues
        result = super().dict(*args, **kwargs)
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}


class ChatHistoryResponse(BaseModel):
    id: int
    user_id: int
    message: str
    is_bot: bool
