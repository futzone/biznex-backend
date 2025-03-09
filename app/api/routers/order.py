from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.models.user import AdminUser
from app.api.routers.admin import get_current_admin_user
from app.api.schemas.order import OrderCreate, Order, OrderItemCreate
from app.api.controllers.order import OrderController
from app.core.databases.postgres import get_general_session

router = APIRouter()


@router.post("/orders", response_model=Order)
async def create_order(
    order_create: OrderCreate,
    session: AsyncSession = Depends(get_general_session),
    current_user: AdminUser = Depends(get_current_admin_user),
):
    controller = OrderController(session)
    order = await controller.create(order_create)
    return order


@router.get("/orders", response_model=Order)
async def get_order(session: AsyncSession = Depends(get_general_session)):
    controller = OrderController(session)
    order = await controller.get_all()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/orders/{order_id}", response_model=Order)
async def update_order(
    order_id: int,
    order_update: OrderCreate,
    session: AsyncSession = Depends(get_general_session),
):
    controller = OrderController(session)
    order = await controller.update(order_id, order_update)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.delete("/orders/{order_id}")
async def delete_order(
    order_id: int, session: AsyncSession = Depends(get_general_session)
):
    controller = OrderController(session)
    success = await controller.delete(order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted successfully"}


@router.get("/orders/user/{user_id}", response_model=list[Order])
async def get_orders_by_user_id(
    user_id: int, session: AsyncSession = Depends(get_general_session)
):
    controller = OrderController(session)
    orders = await controller.get_all_by_user_id(user_id)
    return orders


@router.get("/orders", response_model=list[Order])
async def get_all_orders(session: AsyncSession = Depends(get_general_session)):
    controller = OrderController(session)
    orders = await controller.get_all()
    return orders
