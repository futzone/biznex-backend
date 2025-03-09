from typing import Optional
from pydantic import BaseModel


class DeviceCreateSchema(BaseModel):
    user_id: int
    key: str
    ip_address: Optional[str] = None
    device_name: Optional[str] = None
    device_info: Optional[str] = None

class DeviceResponseSchema(DeviceCreateSchema):
    id: int

    class Config:
        from_attributes = True
