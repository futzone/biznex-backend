import json
import secrets
import bcrypt
from typing import Sequence, Optional
from fastapi import Depends, HTTPException, status

from app.api.models.user import AdminUser, User
from app.api.repositories.warehouse import WarehouseRepository
from app.api.constants.permissions import owner as owner_permission
from app.api.schemas.user import AdminWarehouseResponse
from app.api.schemas.warehouse import (
    WarehouseApplicationCreateSchema,
    WarehouseApplicationUpdateSchema,
    WarehouseApplicationResponseSchema,
    CreateWarehouseRequest,
    UpdateWarehouseRequest,
    WarehouseCreateResponse,
    WarehouseResponse,
)


class WarehouseController:
    def __init__(self, warehouse_repository: WarehouseRepository = Depends()) -> None:
        self.__warehouse_repository = warehouse_repository

    async def get_warehouses(self, limit=5, offset=0) -> Sequence[WarehouseResponse]:
        try:
            warehouses = await self.__warehouse_repository.get_warehouses(limit, offset)

            for warehouse in warehouses:
                for role in warehouse.roles:
                    if role.permissions is None:
                        role.permissions = (
                            {}
                        )
                    elif isinstance(role.permissions, str):
                        role.permissions = json.loads(role.permissions)
                    elif isinstance(role.permissions, dict):
                        role.permissions = {
                            k: (
                                v
                                if isinstance(v, list)
                                else [v] if isinstance(v, (str, bool)) else []
                            )
                            for k, v in role.permissions.items()
                        }

            return warehouses
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid JSON in permissions: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {str(e)}",
            )

    async def get_warehouse_by_id(
            self, warehouse_id: int
    ) -> Optional[WarehouseResponse]:
        warehouse = await self.__warehouse_repository.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Warehouse not found",
            )
        return warehouse

    async def create_warehouse(
            self, warehouse_data: CreateWarehouseRequest, current_user: AdminUser
    ) -> WarehouseCreateResponse:
        if not current_user.is_global_admin:
            raise HTTPException(
                status_code=403, detail="Only global admins can create warehouses"
            )
        generated_password = secrets.token_urlsafe(10)
        hashed_password = bcrypt.hashpw(
            generated_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        owner_data = {
            "phone_number": warehouse_data.owner_phone_number,
            "password": hashed_password,
        }

        owner = owner_permission

        warehouse, owner = (
            await self.__warehouse_repository.create_warehouse_with_owner(
                warehouse_data=warehouse_data.dict(),
                owner_data=owner_data,
                owner_permission=owner,
            )
        )

        return WarehouseCreateResponse(
            id=warehouse.id,
            name=warehouse.name,
            address=warehouse.address,
            description=warehouse.description,
            latitude=warehouse.latitude,
            longitude=warehouse.longitude,
            owner_phone_number=owner.phone_number,
            owner_password=generated_password,
            owner_id=owner.id,
        )

    async def update_warehouse(
            self,
            warehouse_id: int,
            warehouse_data: CreateWarehouseRequest,
            current_user: AdminUser,
    ) -> WarehouseCreateResponse:
        if not current_user.is_global_admin:
            raise HTTPException(
                status_code=403, detail="Only global admins can update warehouses"
            )

        try:
            generated_password = secrets.token_urlsafe(10)
            hashed_password = bcrypt.hashpw(
                generated_password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            owner_data = {
                "phone_number": warehouse_data.owner_phone_number,
                "password": hashed_password,
            }

            updated_warehouse, updated_owner = (
                await self.__warehouse_repository.update_warehouse_with_owner(
                    warehouse_data=warehouse_data.dict(),
                    owner_data=owner_data,
                    warehouse_id=warehouse_id,
                )
            )

            return WarehouseCreateResponse(
                id=updated_warehouse.id,
                name=updated_warehouse.name,
                address=updated_warehouse.address,
                description=updated_warehouse.description,
                latitude=updated_warehouse.latitude,
                longitude=updated_warehouse.longitude,
                owner_phone_number=updated_owner.phone_number,
                owner_password=generated_password,
                owner_id=updated_owner.id,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error updating warehouse: {str(e)}"
            )

    async def delete_warehouse(self, warehouse_id: int) -> Optional[WarehouseResponse]:
        return await self.__warehouse_repository.delete_warehouse(warehouse_id)

    async def get_warehouse_applications(
            self,
    ) -> Sequence[WarehouseApplicationResponseSchema]:
        return await self.__warehouse_repository.get_warehouse_applications()

    async def get_warehouse_application_by_id(
            self, application_id: int
    ) -> Optional[WarehouseApplicationResponseSchema]:
        app = await self.__warehouse_repository.get_warehouse_application_by_id(
            application_id
        )
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="WarehouseApplication not found",
            )
        return app

    async def create_warehouse_application(
            self, data: WarehouseApplicationCreateSchema
    ) -> WarehouseApplicationResponseSchema:
        return await self.__warehouse_repository.create_warehouse_application(data)

    async def update_warehouse_application(
            self, application_id: int, data: WarehouseApplicationUpdateSchema
    ) -> WarehouseApplicationResponseSchema:
        return await self.__warehouse_repository.update_warehouse_application(
            application_id, data
        )

    async def delete_warehouse_application(self, application_id: int) -> None:
        return await self.__warehouse_repository.delete_warehouse_application(
            application_id
        )
