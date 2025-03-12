from typing import List, Optional
from pydantic import BaseModel, Field
from app.api.schemas.user import AdminWarehouseResponse
from app.core.models.enums import WarehouseApplicationStatus


class CreateWarehouseRequest(BaseModel):
    name: str
    address: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    owner_phone_number: str = Field(
        ..., pattern=r"^\+?[1-9]\d{1,14}$"
    )  # Owner's phone number


class WarehouseUpdateSchema(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    owner_id: Optional[int] = None


class WarehouseCreateResponse(BaseModel):
    id: int
    name: str
    address: str
    description: Optional[str]
    latitude: float
    longitude: float
    owner_id: int
    owner_phone_number: str
    owner_password: str

    class Config:
        from_attributes = True


# Foydalanuvchiga tegishli ruxsatlar


class WarehouseResponse(BaseModel):
    id: int
    name: str
    address: str
    description: Optional[str]
    latitude: float
    longitude: float
    owner_id: int
    # roles: Optional[List[AdminWarehouseResponse]] = []

    class Config:
        from_attributes = True


class WarehouseApplicationCreateSchema(BaseModel):
    phone_number: str
    bank_account: str
    image: Optional[str] = None
    status: Optional[WarehouseApplicationStatus] = None

    warehouse_id: int


class WarehouseApplicationUpdateSchema(BaseModel):
    phone_number: Optional[str] = None
    bank_account: Optional[str] = None
    image: Optional[str] = None
    status: Optional[WarehouseApplicationStatus] = None
    warehouse_id: Optional[int] = None

    class Config:
        from_attributes = True


class WarehouseApplicationResponseSchema(WarehouseApplicationCreateSchema):
    id: int
    status: WarehouseApplicationStatus

    class Config:
        from_attributes = True


class UpdateWarehouseRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    address: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    owner_phone_number: Optional[str] = Field(
        None,
        pattern=r"^\+?[1-9]\d{1,14}$",
        description="Owner's phone number in international format",
    )
