from fastapi import Depends
from app.api.repositories.order import OrderRepository
from app.api.schemas.order import OrderCreate, Order
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.databases.postgres import get_general_session


class OrderController:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def create(self, order_create: OrderCreate) -> Order:
        return await OrderRepository(session=self.__session).create(order_create)

    async def update(self, order_id: int, order_update: OrderCreate) -> Order:
        return await OrderRepository(session=self.__session).update(
            order_id, order_update
        )

    async def delete(self, order_id: int) -> bool:
        return await OrderRepository(session=self.__session).delete(order_id)

    async def get_by_id(self, order_id: int) -> Order:
        return await OrderRepository(session=self.__session).get_by_id(order_id)

    async def get_all(self) -> list[Order]:
        return await OrderRepository(session=self.__session).get_all()

    async def get_all_by_user_id(self, user_id: int) -> list[Order]:
        return await OrderRepository(session=self.__session).get_all_by_user_id(user_id)
