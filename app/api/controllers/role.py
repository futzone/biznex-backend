import json
from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.repositories.role import AdminWarehouseRepository
from app.api.schemas.role import (
    AdminWarehouseCreate,
    AdminWarehouseUpdate,
    AdminWarehouseResponse,
)


class AdminWarehouseController:
    def __init__(self, session: AsyncSession):
        self.repository = AdminWarehouseRepository(session)

    async def create_admin_warehouse(
        self, data: AdminWarehouseCreate
    ) -> AdminWarehouseCreate:
        await self.repository.create_admin_warehouse(
            warehouse_id=data.warehouse_id,
            role_name=data.role_name,
            permissions=data.permissions,
        )
        return data

    async def get_admin_warehouses(self) -> List[AdminWarehouseResponse]:
        admin_warehouses = await self.repository.get_all_admin_warehouses()

        if not admin_warehouses:
            raise HTTPException(status_code=404, detail="AdminWarehouses not found")

        return [
            AdminWarehouseResponse.parse_obj(
                {
                    "id": admin_warehouse.id,
                    "warehouse_id": admin_warehouse.warehouse_id,
                    "role_name": admin_warehouse.name,
                    "permissions": (
                        json.loads(admin_warehouse.permissions)
                        if isinstance(admin_warehouse.permissions, str)
                        else admin_warehouse.permissions
                    ),
                }
            )
            for admin_warehouse in admin_warehouses
        ]

    async def get_admin_warehouses_with_warehouse_id(
        self, warehouse_id: int
    ) -> List[AdminWarehouseResponse]:
        admin_warehouses = await self.repository.get_admin_warehouses(warehouse_id)

        if not admin_warehouses:
            raise HTTPException(status_code=404, detail="AdminWarehouse not found")

        return [
            AdminWarehouseResponse.parse_obj(
                {
                    "id": admin_warehouse.id,
                    "warehouse_id": admin_warehouse.warehouse_id,
                    "role_name": admin_warehouse.name,
                    "permissions": (
                        json.loads(admin_warehouse.permissions)
                        if isinstance(admin_warehouse.permissions, str)
                        else admin_warehouse.permissions
                    ),
                }
            )
            for admin_warehouse in admin_warehouses
        ]

    async def update_permissions(
        self, id: int, data: AdminWarehouseUpdate
    ) -> AdminWarehouseUpdate:
        updated_admin_warehouse = await self.repository.update_permissions(
            id, data.permissions, data.role_name
        )
        return AdminWarehouseUpdate(
            role_name=updated_admin_warehouse.get("name"),
            permissions=updated_admin_warehouse.get("permissions"),
        )

    async def delete_admin_warehouse(self, admin_warehouse_id: int):
        await self.repository.delete_admin_warehouse(admin_warehouse_id)
