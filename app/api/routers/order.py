from typing import Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from app.api.controllers.user import UserController
from app.api.schemas.order import OrderCreate, Order
from app.api.controllers.order import OrderController
from app.core.databases.postgres import get_general_session
from database.init import get_postgres
from models.pagination_model import PaginationModel
from models.user_order_model import UserOrderModel
from router.order_api_router import OrderApiRouter

router = APIRouter()


@router.post("/orders")
async def create_order(request: Request, model: UserOrderModel, controller: UserController = Depends(), pool: asyncpg.Pool = Depends(get_postgres)):
    return await OrderApiRouter.create_order(controller=controller, request=request, model=model, pool=pool)


@router.get("/orders/{offset}/{limit}/{status}", response_model=None)
async def get_order(request: Request, offset: int, limit: int, status: Optional[str] = None, controller: UserController = Depends(), pool: asyncpg.Pool = Depends(get_postgres)):
    model = PaginationModel(offset=offset, limit=limit, status=status)
    return await OrderApiRouter.get_user_orders(controller=controller, request=request, model=model, pool=pool)


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
