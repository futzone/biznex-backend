from typing import Optional
from pydantic import BaseModel


class ColorCreateSchema(BaseModel):
    name: str
    hex_code: str


class ColorUpdateSchema(BaseModel):
    name: Optional[dict[str, str]] = None
    hex_code: Optional[str] = None

    class Config:
        from_attributes = True


class ColorResponseSchema(ColorCreateSchema):
    id: int

    class Config:
        from_attributes = True


class ColorLanguageResponseSchema(ColorResponseSchema):
    name: dict[str, str]

