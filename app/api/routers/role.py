from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.api.controllers.role import AdminWarehouseController
from app.api.models.user import AdminUser
from app.api.schemas.role import (
    AdminWarehouseCreate,
    AdminWarehouseUpdate,
    AdminWarehouseResponse,
)
from app.api.utils.permission_checker import check_permission
from app.api.utils.user import AuthUtils
from app.core.databases.postgres import get_general_session


router = APIRouter()


@router.post("/admin_warehouse", response_model=AdminWarehouseCreate)
async def create_admin_warehouse(
    request: Request,
    data: AdminWarehouseCreate,
    db: AsyncSession = Depends(get_general_session),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
    session: AsyncSession = Depends(get_general_session),
):
    warehouse_id = request.headers.get('warehouse_id')
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="admin_warehouse",
        action="create",
    )

    controller = AdminWarehouseController(db)
    return await controller.create_admin_warehouse(data)


@router.get("/admin_warehouse", response_model=List[AdminWarehouseResponse])
async def get_admin_warehouses(
    db: AsyncSession = Depends(get_general_session),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
):
    if not current_admin.is_global_admin:
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail="You are teapot).",
        )

    controller = AdminWarehouseController(db)
    return await controller.get_admin_warehouses()


@router.get(
    "/admin_warehouse/{warehouse_id}", response_model=List[AdminWarehouseResponse]
)
async def get_admin_warehouse(
    warehouse_id: int,
    db: AsyncSession = Depends(get_general_session),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
    session: AsyncSession = Depends(get_general_session),
):

    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="admin_warehouse",
        action="get",
    )

    controller = AdminWarehouseController(db)
    return await controller.get_admin_warehouses_with_warehouse_id(warehouse_id)


@router.put(
    "/admin_warehouse/{admin_warehouse_id}", response_model=AdminWarehouseUpdate
)
async def update_permissions(
    request: Request,
    admin_warehouse_id: int,
    data: AdminWarehouseUpdate,
    db: AsyncSession = Depends(get_general_session),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
    session: AsyncSession = Depends(get_general_session),
):
    warehouse_id = request.headers.get('warehouse_id')
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="admin_warehouse",
        action="update",
    )

    controller = AdminWarehouseController(db)
    return await controller.update_permissions(admin_warehouse_id, data)


@router.delete("/admin_warehouse/{admin_warehouse_id}", status_code=204)
async def delete_admin_warehouse(
    request: Request,
    admin_warehouse_id: int,
    db: AsyncSession = Depends(get_general_session),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
    session: AsyncSession = Depends(get_general_session),
):
    warehouse_id = request.headers.get('warehouse_id')
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="admin_warehouse",
        action="delete",
    )

    controller = AdminWarehouseController(db)
    await controller.delete_admin_warehouse(admin_warehouse_id)
