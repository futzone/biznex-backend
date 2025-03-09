from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy import insert
from sqlalchemy.orm import selectinload

from app.api.models.user import AdminUser
from app.core.databases.postgres import get_general_session
from app.api.schemas.warehouse import WarehouseResponse
from app.api.models.warehouse import AdminWarehouse, Warehouse, admin_warehouse_roles


class WarehouseRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def get_warehouses(self, limit, offset) -> Sequence[WarehouseResponse]:
        result = await self.__session.execute(
            select(Warehouse)
            .options(selectinload(Warehouse.roles).selectinload(AdminWarehouse.admins))
            .limit(limit)
            .offset(offset)
        )
        return [
            WarehouseResponse.model_validate(warehouse)
            for warehouse in result.scalars()
        ]

    async def get_warehouse_by_id(self, warehouse_id: int):
        stmt = (
            select(Warehouse)
            .options(selectinload(Warehouse.roles))
            .where(Warehouse.id == warehouse_id)
        )
        result = await self.__session.execute(stmt)
        warehouse = result.scalar_one_or_none()
        return WarehouseResponse.model_validate(warehouse) if warehouse else None

    async def create_warehouse_with_owner(
        self, warehouse_data: dict, owner_data: dict, owner_permission: dict
    ) -> tuple[Warehouse, AdminUser]:
        try:
            new_owner = AdminUser(
                full_name=f"Owner {warehouse_data['name']}",
                phone_number=owner_data["phone_number"],
                password=owner_data["password"],
                is_global_admin=False,
            )
            self.__session.add(new_owner)
            await self.__session.flush() 

            new_warehouse = Warehouse(
                name=warehouse_data["name"],
                address=warehouse_data["address"],
                description=warehouse_data.get("description"),
                latitude=warehouse_data["latitude"],
                longitude=warehouse_data["longitude"],
                owner_phone_number=owner_data["phone_number"],
                owner_id=new_owner.id,
            )
            self.__session.add(new_warehouse)
            await self.__session.flush()

            admin_warehouse = AdminWarehouse(
                warehouse_id=new_warehouse.id,
                name="Owner",
                permissions=owner_permission,
            )
            self.__session.add(admin_warehouse)
            await self.__session.commit()

            try:
                insert_query = insert(admin_warehouse_roles).values(
                    admin_id=new_owner.id,
                    warehouse_role_id=admin_warehouse.id,
                )
                await self.__session.execute(insert_query)
                await self.__session.commit()
            except Exception as e:
                raise e

            return new_warehouse, new_owner
        except Exception as e:
            await self.__session.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def update_warehouse_with_owner(
        self, warehouse_data: dict, owner_data: dict, warehouse_id: int
    ):
        stmt = select(Warehouse).filter(Warehouse.id == warehouse_id)
        warehouse = await self.__session.scalar(stmt)

        if warehouse is None:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        warehouse.name = warehouse_data["name"]
        warehouse.address = warehouse_data["address"]
        warehouse.description = warehouse_data.get("description", warehouse.description)
        warehouse.latitude = warehouse_data["latitude"]
        warehouse.longitude = warehouse_data["longitude"]

        owner_stmt = select(AdminUser).filter(AdminUser.id == warehouse.owner_id)
        owner = await self.__session.scalar(owner_stmt)

        if owner is None:
            raise HTTPException(status_code=404, detail="Owner not found")

        owner.phone_number = owner_data["phone_number"]
        owner.password = owner_data["password"]
        self.__session.add(warehouse)
        self.__session.add(owner)
        await self.__session.flush()

        return warehouse, owner

    async def delete_warehouse(self, warehouse_id: int) -> Optional[WarehouseResponse]:
        result = await self.__session.execute(
            select(Warehouse).where(Warehouse.id == warehouse_id)
        )
        warehouse = result.scalar_one_or_none()
        if warehouse:
            await self.__session.delete(warehouse)
            await self.__session.commit()
            return WarehouseResponse.model_validate(warehouse)
        return None
