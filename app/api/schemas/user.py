from datetime import datetime, timedelta
from decimal import Decimal
import re
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional


class Sendticket(BaseModel):
    name: str
    email: str

class SendFormticket(BaseModel):
    name: str
    email: str
    message: str

class UserBase(BaseModel):
    id: int
    full_name: str
    phone_number: str
    profile_picture: Optional[str] = None
    is_active: bool = False


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=50)
    phone_number: str = Field(..., min_length=9, max_length=15)
    password: str = Field(..., min_length=8, max_length=50)

    @validator("phone_number")
    def validate_phone_number(cls, v):
        if not re.match(r"^[+]?[0-9]{9,14}$", v):
            raise ValueError("Invalid phone number format")
        return v


class AdminCreateRequest(BaseModel):
    phone_number: str
    password: str


class UserLogin(BaseModel):
    phone_number: str
    password: str


class OTPVerify(BaseModel):
    user_id: int
    otp: str


class UserResponse(BaseModel):
    id: int
    phone_number: str

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    permission_id: Optional[int] = None
    profile_picture: Optional[str] = None
    is_active: Optional[bool] = None


class DeviceInfoSchema(BaseModel):
    device_name: str
    user_agent: str
    ip_address: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    phone_number: str
    profile_picture: Optional[str]

    class Config:
        from_attributes = True


class UserInDB(User):
    hashed_password: str


class AdminWarehouseRole(BaseModel):
    id: int
    name: str
    permissions: dict
    is_owner: bool


class AdminUserCreate(BaseModel):
    full_name: str
    phone_number: str
    profile_picture: Optional[str] = None
    is_global_admin: bool
    warehouse_id: int
    warehouse_role_id: int


class AdminUserResponse(BaseModel):
    id: int
    full_name: str
    phone_number: str
    profile_picture: Optional[str] = None


class WarehouseRoleResponse(BaseModel):
    id: int
    name: str
    permissions: Dict[str, list]
    is_owner: bool

    class Config:
        from_attributes = True


class WarehousePermissionResponse(BaseModel):
    permission_name: str  # Permission nomi
    # Permission turi (misol: "update", "delete", va boshqalar)
    permission_type: str

    class Config:
        from_attributes = True


class AdminWarehouseResponse(BaseModel):
    id: int
    warehouse_id: int
    name: str
    is_owner: bool
    permissions: Dict[str, List[str]] = Field(default={})

    class Config:
        from_attributes = True


class WarehouseCreateResponsee(BaseModel):
    id: int
    name: str
    address: str
    description: Optional[str]
    latitude: float
    longitude: float
    owner_id: int
    owner_phone_number: str

    class Config:
        from_attributes = True


class AdminUserResponse(BaseModel):
    id: int
    full_name: str
    phone_number: str
    is_global_admin: bool
    profile_picture: Optional[str] = None
    password: Optional[str] = None
    warehouses: List[WarehouseCreateResponsee] = []  # warehouses ni kiritish

    class Config:
        from_attributes = True


class AdminUserResponsee(BaseModel):
    id: int
    full_name: str
    phone_number: str
    is_global_admin: bool
    profile_picture: Optional[str] = None
    role_name: str


class BaseStats(BaseModel):
    growth_rate: float
    total_count: int


class AdminDashboardResponse(BaseModel):
    orders: BaseStats
    products: BaseStats
    pending_orders: BaseStats
    completed_orders: BaseStats


class TopSellerFilterRequest(BaseModel):
    start_date: Optional[datetime] = Field(
        default_factory=lambda: datetime.now() - timedelta(days=30),
        description="Start date for the report (default: 30 days ago)"
    )
    end_date: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(),
        description="End date for the report (default: current date)"
    )
    
class TopSellerResponse(BaseModel):
    id: int
    full_name: str
    phone_number: str
    is_global_admin: bool
    profile_picture: Optional[str] = None
    role_name: str

    order_count: int = Field(description="Number of completed orders")
    items_sold: int = Field(description="Total number of items sold")
    total_revenue: Decimal = Field(description="Total revenue generated (without discounts)")
    total_revenue_with_discount: Decimal = Field(description="Total revenue generated (with discounts)")
    total_profit: Decimal = Field(description="Estimated profit (revenue with discount - cost)")
    average_order_value: Decimal = Field(description="Average value per order")