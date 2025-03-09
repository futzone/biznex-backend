import logging
from typing import List, Sequence, Optional
from app.api.controllers.admin import AdminController
from app.api.models.user import AdminUser
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.controllers.warehouse import WarehouseController
from app.api.schemas.user import WarehouseRoleResponse
from app.api.schemas.warehouse import (
    CreateWarehouseRequest,
    UpdateWarehouseRequest,
    WarehouseCreateResponse,
    WarehouseResponse,
    WarehouseUpdateSchema,
)
from app.api.utils.user import AuthUtils

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.databases.postgres import get_general_session

router = APIRouter()


@router.get(
    "/",
    response_model=Sequence[WarehouseResponse],
    status_code=status.HTTP_200_OK,
)
async def get_warehouses(
    limit: int = Query(10, alias="limit", ge=1),
    offset: int = Query(0, alias="offset", ge=0),
    controller: WarehouseController = Depends(),
) -> Sequence[WarehouseResponse]:
    return await controller.get_warehouses(limit, offset)


@router.post("/", response_model=WarehouseCreateResponse)
async def create_warehouse(
    warehouse_data: CreateWarehouseRequest,
    request: Request,
    controller: WarehouseController = Depends(),
    admin_controller: AdminController = Depends(),
    session: AsyncSession = Depends(get_general_session),
):
    current_user = await admin_controller.get_current_admin_user(
        session=session, request=request
    )
    logging.info(f"Received warehouse data: {warehouse_data}")
    return await controller.create_warehouse(warehouse_data, current_user)


@router.patch("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: int,
    warehouse_data: UpdateWarehouseRequest,
    request: Request,
    controller: WarehouseController = Depends(),
    admin_controller: AdminController = Depends(),
    session: AsyncSession = Depends(get_general_session),
):
    current_user = await admin_controller.get_current_admin_user(
        session=session, request=request
    )
    return await controller.update_warehouse(
        warehouse_id=warehouse_id,
        warehouse_data=warehouse_data,
        current_user=current_user,
    )


@router.delete(
    "/{warehouse_id}/",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete warehouse by id. If deleted successfully, it will return 204 status code",
    description="Delete warehouse by id. If deleted successfully, it will return 204 status code",
)
async def delete_warehouse(
    warehouse_id: int,
    controller: WarehouseController = Depends(),
) -> Optional[WarehouseResponse]:
    return await controller.delete_warehouse(warehouse_id)
