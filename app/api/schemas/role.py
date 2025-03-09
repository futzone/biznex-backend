from typing import Dict, List
from pydantic import BaseModel


class AdminWarehouseBase(BaseModel):
    warehouse_id: int
    role_name: str
    permissions: Dict[str, List[str]]  # Permissions JSON formatida

    class Config:
        from_attributes = True


class AdminWarehouseCreate(AdminWarehouseBase):
    pass


class AdminWarehouseResponse(BaseModel):
    id: int
    warehouse_id: int
    role_name: str
    permissions: Dict[str, List[str]]  # Permissions JSON formatida

    class Config:
        from_attributes = True


class AdminWarehouseUpdate(BaseModel):
    role_name: str
    permissions: Dict[str, list]
