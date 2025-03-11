from typing import Any, Coroutine, List

from fastapi import HTTPException

from fastapi import Depends

from app.api.models import AdminOrder
from app.api.repositories.adminorder import AdminOrderRepository
from app.api.schemas.order import AdminOrderResponse, OrderItemRequest, AdminOrderUpdate
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.check_language import check_language
from app.core.databases.postgres import get_general_session


class AdminOrderController:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session
        self.__admin_order_repository = AdminOrderRepository(session=self.__session)

    async def get_admin_current_order(self, admin_id: int, language: str) -> AdminOrderResponse | None:
        await check_language(language)
        result = await self.__admin_order_repository.get_admin_current_order(admin_id, language)

        if result:
            return result
        raise HTTPException(
            status_code=400,
            detail="You don't have an open order."
        )

    async def get_all_closed_orders(self, admin_id: int, language: str, limit: int, offset: int) -> List[AdminOrderResponse] | None:
        result = await self.__admin_order_repository.get_all_closed_orders(admin_id, language, limit, offset)

        if result:
            return result
        return []

    async def get_order_by_id(self, order_id: int, language: str) -> AdminOrderResponse | None:
        await check_language(language)
        result = await self.__admin_order_repository.get_order_by_id(order_id, language)

        if result:
            return result
        raise HTTPException(
            status_code=400,
            detail="Order not found."
        )

    async def create_admin_order(self, by, language, warehouse_id) -> AdminOrderResponse:
        await check_language(language)
        if await self.__admin_order_repository.get_admin_current_order(admin_id=by, language=language):
            raise HTTPException(
                status_code=400,
                detail="You have an open order. Please complete or cancel it before creating a new one."
            )
        else:
            return await self.__admin_order_repository.create_new_order(by, warehouse_id)

    async def create_complete_order(self, admin_id: int, data: OrderItemRequest, language: str, warehouse_id: int):
        await check_language(language)
        results = []
        for order_data in data:
            result = await self.__admin_order_repository.create_complete_order(
                admin_id=admin_id,
                data=order_data,
                warehouse_id=warehouse_id,
                language=language
            )
            results.append(result)

        return results

    async def close_current_order(self, admin_id: int, data: AdminOrderUpdate, language: str) -> dict | None:
        await check_language(language)
        if await self.__admin_order_repository.get_admin_current_order(admin_id=admin_id, language=language):
            result = await self.__admin_order_repository.update_status_order(admin_id, data)
            return result
        raise HTTPException(
            status_code=400,
            detail="You don't have an open order."
        )
