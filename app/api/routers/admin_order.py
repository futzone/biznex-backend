from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy import alias
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import AdminOrder
from app.api.models.user import AdminUser
from app.api.routers.admin import get_current_admin_user
from app.api.schemas.order import AdminOrderUpdate, CompleteOrderRequest, OrderCreate, Order, OrderItemCreate, AdminOrderResponse, AdminOrderCreate
from app.api.controllers.admin_order import AdminOrderController
from app.api.utils.permission_checker import check_permission
from app.core.databases.postgres import get_general_session
from app.core.models.enums import AdminOrderStatusEnum

router = APIRouter()


@router.get("/all-orders", response_model=List[AdminOrderResponse] | None)
async def get_all_closed_orders(
        session: AsyncSession = Depends(get_general_session),
        current_user: AdminUser = Depends(get_current_admin_user),
        limit: int = Query(10, alias="limit", ge=1),
        offset: int = Query(0, alias="offset", ge=0),
        language: str = Header(..., alias="language"),
):
    controller = AdminOrderController(session)

    return await controller.get_all_closed_orders(current_user.id, language, limit, offset)


@router.get("/order/{order_id}", response_model=AdminOrderResponse | None)
async def get_order_by_id(
        order_id: int,
        session: AsyncSession = Depends(get_general_session),
        current_user: AdminUser = Depends(get_current_admin_user),
        language: str = Header(None, alias="language"),
):
    controller = AdminOrderController(session)
    return await controller.get_order_by_id(order_id, language)


@router.get("/order", response_model=AdminOrderResponse | None)
async def get_admin_order(
        session: AsyncSession = Depends(get_general_session),
        current_user: AdminUser = Depends(get_current_admin_user),
        language: str = Header(..., alias="language"),
):
    controller = AdminOrderController(session)

    return await controller.get_admin_current_order(current_user.id, language)


@router.post("/order", response_model=AdminOrderCreate)
async def create_order(
        session: AsyncSession = Depends(get_general_session),
        current_user: AdminUser = Depends(get_current_admin_user),
        language: str = Header(..., alias="language"),
        warehouse_id: int = Header(..., alias="warehouse_id"),
) -> AdminOrderResponse:
    controller = AdminOrderController(session)
    try:
        return await controller.create_admin_order(current_user.id, language, warehouse_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/order", response_model=dict | None)
async def close_admin_order(
        data: AdminOrderUpdate,
        session: AsyncSession = Depends(get_general_session),
        current_user: AdminUser = Depends(get_current_admin_user),
        language: str = Header(..., alias="language"),
) -> dict | None:
    controller = AdminOrderController(session)
    return await controller.close_current_order(current_user.id, data, language=language)


@router.post(
    "/offline/order",
)
async def create_complate_order(
        order_data: List[CompleteOrderRequest],
        session: AsyncSession = Depends(get_general_session),
        current_user: AdminUser = Depends(get_current_admin_user),
        language: str = Header(..., alias="language"),
        warehouse_id: int = Header(..., alias="warehouse_id"),
):
    controller = AdminOrderController(session)
    return await controller.create_complete_order(data=order_data, admin_id=current_user.id, language=language, warehouse_id=warehouse_id)
