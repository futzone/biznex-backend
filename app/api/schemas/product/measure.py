from typing import Optional
from pydantic import BaseModel


class MeasureCreateSchema(BaseModel):
    name: str


class MeasureUpdateSchema(BaseModel):
    name: Optional[str] = None

    class Config:
        from_attributes = True


class MeasureResponseSchema(MeasureCreateSchema):
    id: int

    class Config:
        from_attributes = True
