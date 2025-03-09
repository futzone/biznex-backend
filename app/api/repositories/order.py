from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.models.order import Order, OrderItem
from app.api.schemas.order import OrderCreate, OrderItemCreate
from app.core.databases.postgres import get_general_session


class OrderRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.db = session

    async def get_by_id(self, order_id: int) -> Order:
        result = await self.db.execute(select(Order).filter(Order.id == order_id))
        return result.scalars().first()

    async def create(self, order_create: OrderCreate) -> Order:
        order = Order(**order_create.dict())
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)

        for item in order_create.items:
            order_item = OrderItem(**item.dict(), order_id=order.id)
            self.db.add(order_item)
        await self.db.commit()

        return order

    async def update(self, order_id: int, order_update: OrderCreate) -> Order:
        order = await self.get_by_id(order_id)
        if order:
            for key, value in order_update.dict(exclude_unset=True).items():
                setattr(order, key, value)
            await self.db.commit()
            await self.db.refresh(order)
        return order

    async def delete(self, order_id: int) -> bool:
        order = await self.get_by_id(order_id)
        if order:
            await self.db.delete(order)
            await self.db.commit()
            return True
        return False

    async def get_all(self) -> list[Order]:
        result = await self.db.execute(select(Order))
        return result.scalars().all()

    async def get_all_by_user_id(self, user_id: int) -> list[Order]:
        result = await self.db.execute(select(Order).filter(Order.user_id == user_id))
        return result.scalars().all()
