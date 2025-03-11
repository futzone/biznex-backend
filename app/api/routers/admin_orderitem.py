from typing import Any, Coroutine, List

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import alias
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.api.controllers.admin_orderitem import AdminOrderItemController
from app.api.models import AdminOrder
from app.api.models.user import AdminUser
from app.api.routers.admin import get_current_admin_user
from app.api.schemas.order import AdminOrderItemResponse, AdminOrderItemReturnSchema, AdminOrderItemSchema, AdminOrderResponse, BatchOrderItemsRequest, OrderItemRequest
from app.api.controllers.admin_order import AdminOrderController
from app.api.utils.permission_checker import check_permission
from app.core.databases.postgres import get_general_session
from app.core.models.enums import AdminOrderStatusEnum
from fastapi import status

router = APIRouter()


@router.get("/orderitem", response_model=List[AdminOrderItemResponse] | None)
async def get_order_items(
        session: AsyncSession = Depends(get_general_session),
        current_admin: AdminUser = Depends(get_current_admin_user),
        language: str = Header(..., alias="language"),
) -> List[AdminOrderItemResponse]:
    controller = AdminOrderItemController(session)

    return await controller.get_admin_order_items(current_admin.id, language)


@router.post("/orderitem", response_model=List[AdminOrderItemResponse])
async def add_item_to_order(
        request: Request,
        order_id: int,
        items_data: List[OrderItemRequest],
        language: str = Header(..., alias="language"),
        session: AsyncSession = Depends(get_general_session),
        current_admin: AdminUser = Depends(get_current_admin_user),
) -> List[AdminOrderItemResponse]:

    controller = AdminOrderItemController(session)
    warehouse_id = int(request.headers.get('warehouse_id'))

    return await controller.add_items_to_order(items=items_data, order_id=order_id, admin_id=current_admin.id, language=language, warehouse_id=warehouse_id)



@router.post("/orderitem/{order_item_id}/return", response_model=AdminOrderItemResponse)
async def return_order_item(
    order_item_id: int,
    data: AdminOrderItemReturnSchema,
    session: AsyncSession = Depends(get_general_session),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    controller = AdminOrderItemController(session)
    return await controller.return_order_item(
        order_item_id=order_item_id,
        admin_id=current_admin.id,
        data=data
    )


@router.patch("/orderitem/{order_item_id}", response_model=AdminOrderItemResponse)
async def update_order_item(
        order_item_id: int,
        quantity: float,
        session: AsyncSession = Depends(get_general_session),
        current_admin: AdminUser = Depends(get_current_admin_user),
        language: str = Header(..., alias="language"),
) -> AdminOrderItemResponse:

    controller = AdminOrderItemController(session)

    return await controller.update_order_item(order_item_id=order_item_id, quantity=quantity, admin_id=current_admin.id, language=language)

@router.delete("/orderitem/{order_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order_item(
        order_item_id: int,
        session: AsyncSession = Depends(get_general_session),
        current_admin: AdminUser = Depends(get_current_admin_user),
        language: str = Header(..., alias="language"),
) -> None:

    controller = AdminOrderItemController(session)

    return await controller.delete_order_item(order_item_id=order_item_id, admin_id=current_admin.id, language=language)