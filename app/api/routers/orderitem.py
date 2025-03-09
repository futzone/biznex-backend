from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.order import OrderItemCreate, OrderItem
from app.api.controllers.orderitem import OrderItemController
from app.core.databases.postgres import get_general_session

router = APIRouter()


@router.post("/{order_id}", response_model=OrderItem)
async def create_order_item(
    order_item_create: OrderItemCreate,
    session: AsyncSession = Depends(get_general_session),
):
    controller = OrderItemController(session)
    order_item = await controller.create_order_item(order_item_create)
    return order_item


@router.get("/{order_item_id}", response_model=OrderItem)
async def get_order_item(
    order_item_id: int, session: AsyncSession = Depends(get_general_session)
):
    controller = OrderItemController(session)
    order_item = await controller.get_order_item(order_item_id)
    if not order_item:
        raise HTTPException(status_code=404, detail="Order item not found")
    return order_item


@router.put("/{order_item_id}", response_model=OrderItem)
async def update_order_item(
    order_item_id: int,
    order_item_update: OrderItemCreate,
    session: AsyncSession = Depends(get_general_session),
):
    controller = OrderItemController(session)
    order_item = await controller.update_order_item(order_item_id, order_item_update)
    if not order_item:
        raise HTTPException(status_code=404, detail="Order item not found")
    return order_item


@router.delete("/{order_item_id}")
async def delete_order_item(
    order_item_id: int, session: AsyncSession = Depends(get_general_session)
):
    controller = OrderItemController(session)
    success = await controller.delete_order_item(order_item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Order item not found")
    return {"message": "Order item deleted successfully"}


@router.get("/", response_model=list[OrderItem])
async def get_all_order_items(session: AsyncSession = Depends(get_general_session)):
    controller = OrderItemController(session)
    order_items = await controller.get_all_order_items()
    return order_items
