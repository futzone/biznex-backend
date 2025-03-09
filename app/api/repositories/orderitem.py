from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.databases.postgres import get_general_session
from app.api.models.order import OrderItem
from app.api.schemas.order import OrderItemCreate


class OrderItemRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.db = session

    async def get_by_id(self, order_item_id: int) -> OrderItem:
        result = await self.db.execute(
            select(OrderItem).filter(OrderItem.id == order_item_id)
        )
        return result.scalars().first()

    async def create(self, order_item_create: OrderItemCreate) -> OrderItem:
        order_item = OrderItem(**order_item_create.dict())
        self.db.add(order_item)
        await self.db.commit()
        await self.db.refresh(order_item)
        return order_item

    async def update(
        self, order_item_id: int, order_item_update: OrderItemCreate
    ) -> OrderItem:
        order_item = await self.get_by_id(order_item_id)
        if order_item:
            for key, value in order_item_update.dict(exclude_unset=True).items():
                setattr(order_item, key, value)
            await self.db.commit()
            await self.db.refresh(order_item)
        return order_item

    async def delete(self, order_item_id: int) -> bool:
        order_item = await self.get_by_id(order_item_id)
        if order_item:
            await self.db.delete(order_item)
            await self.db.commit()
            return True
        return False

    async def get_all_by_order_id(self, order_id: int) -> list[OrderItem]:
        result = await self.db.execute(
            select(OrderItem).filter(OrderItem.order_id == order_id)
        )
        return result.scalars().all()
