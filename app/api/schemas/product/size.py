from typing import Optional, Dict
from pydantic import BaseModel, Field


class SizeCreateSchema(BaseModel):
    size: str
    description: Optional[str] = None
    warehouse_id: int


class SizeUpdateSchema(BaseModel):
    size: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SizeResponseSchema(SizeCreateSchema):
    id: int

    class Config:
        from_attributes = True


class SizeCreateResponseSchema(BaseModel):
    id: int
    description: Optional[Dict[str, str]]
    size: str
    warehouse_id: int

    class Config:
        from_attributes = True


class SizeLanguageResponseSchema(SizeResponseSchema):
    description: dict[str, str] = Field(default_factory=dict)
