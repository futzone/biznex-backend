import json
from sqlite3 import IntegrityError
from typing import List
from fastapi import HTTPException
from sqlalchemy import update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import NoResultFound
from app.api.models.warehouse import AdminWarehouse


class AdminWarehouseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    async def create_admin_warehouse(
        self, warehouse_id: int, role_name: str, permissions: dict
    ):
        try:
            existing_warehouse = await self.session.execute(
                select(AdminWarehouse).filter(
                    AdminWarehouse.warehouse_id == warehouse_id
                )
            )
            existing_warehouse = existing_warehouse.scalars().first()

            if not existing_warehouse:
                raise HTTPException(status_code=404, detail="Warehouse not found.")

            # Permissionsni JSON formatiga aylantirish
            # if isinstance(permissions, dict):
            #     permissions = json.dumps(
            #         permissions
            #     )  

            stmt = insert(AdminWarehouse).values(
                warehouse_id=warehouse_id,
                name=role_name,
                permissions=permissions,
            )
            await self.session.execute(stmt)
            await self.session.commit()

        except IntegrityError as e:
            if "ForeignKeyViolationError" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail="Foreign key constraint violation. Ensure the referenced warehouse exists.",
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error occurred: " + str(e))

    async def get_all_admin_warehouses(self) -> List[AdminWarehouse]:
        query = select(AdminWarehouse)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_admin_warehouses(self, warehouse_id: int) -> List[AdminWarehouse]:
        result = await self.session.execute(
            select(AdminWarehouse).where(AdminWarehouse.warehouse_id == warehouse_id)
        )
        return result.scalars().all()

    async def update_permissions(
        self, id: int, new_permissions: dict, new_role_name: str
    ):
        stmt = (
            update(AdminWarehouse)
            .where(AdminWarehouse.id == id)
            .values(
                permissions=json.dumps(new_permissions),  
                name=new_role_name,
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

        try:
            result = await self.session.execute(
                select(AdminWarehouse).where(AdminWarehouse.id == id)
            )
            updated_admin_warehouse = (
                result.scalars().first()
            )
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Admin Warehouse not found")

        if not updated_admin_warehouse:
            raise HTTPException(status_code=404, detail="Admin Warehouse not found")

        return {
            "id": updated_admin_warehouse.id,
            "warehouse_id": updated_admin_warehouse.id,
            "name": updated_admin_warehouse.name,
            "permissions": json.loads(
                updated_admin_warehouse.permissions
            ),
        }

    async def delete_admin_warehouse(self, admin_warehouse_id: int):
        stmt = delete(AdminWarehouse).filter(
            AdminWarehouse.id == admin_warehouse_id,
        )
        await self.session.execute(stmt)
        await self.session.commit()
