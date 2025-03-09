from typing import Any, Coroutine, List

from fastapi import HTTPException

from fastapi import Depends

from app.api.models import AdminOrder
from app.api.models.warehouse import admin_warehouse_roles
from app.api.repositories.adminorder import AdminOrderRepository
from app.api.repositories.adminorderitem import AdminOrderItemRepository
from app.api.schemas.order import AdminOrderItemResponse, AdminOrderItemReturnSchema, AdminOrderResponse, OrderItemRequest
from app.api.schemas.order import AdminOrderItemResponse, AdminOrderResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.check_language import check_language
from app.core.databases.postgres import get_general_session


class AdminOrderItemController:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session
        self.__admin_order_item_repository = AdminOrderItemRepository(session=self.__session)
        self.__admin_order_repository = AdminOrderRepository(session=self.__session)

    async def get_admin_order_items(self, admin_id: int, language: str) -> List[AdminOrderItemResponse]:
        await check_language(language)
        result = await self.__admin_order_item_repository.get_admin_order_items(admin_id, language)
        if result:
            return result
        raise HTTPException(
            status_code=400,
            detail="You don't have an open order."
        )

    async def add_items_to_order(
        self, 
        admin_id: int, 
        items: List[OrderItemRequest], 
        order_id: int, 
        language: str, 
        warehouse_id: int
    ) -> List[AdminOrderItemResponse]:
        order = await self.__admin_order_repository.get_admin_current_order(admin_id, language=language)
        if order.by != admin_id:
            raise HTTPException(
                status_code=400,
                detail="You don't have an open order."
            )
        
        await check_language(language)
        
        return await self.__admin_order_item_repository.add_items_to_order(
            items=items, 
            order_id=order_id, 
            language=language, 
            warehouse_id=warehouse_id
        )
    
    async def return_order_item(self, admin_id: int, order_item_id: int, data: AdminOrderItemReturnSchema) -> AdminOrderItemResponse:
        return await self.__admin_order_item_repository.return_order_item(order_item_id, data)



    async def delete_order_item(self, admin_id: int, order_item_id: int, language: str) -> None:
        await check_language(language)
        order = await self.__admin_order_repository.get_admin_current_order(admin_id, language=language)
        if order.by != admin_id:
            raise HTTPException(
                status_code=400,
                detail="You don't have an open order."
            )
        return await self.__admin_order_item_repository.delete_order_item(admin_id, order_item_id)

    async def update_order_item(self, admin_id: int, order_item_id: int, quantity: float, language: str) -> AdminOrderItemResponse:
        await check_language(language)
        order = await self.__admin_order_repository.get_admin_current_order(admin_id, language=language)
        if order.by != admin_id:
            raise HTTPException(
                status_code=400,
                detail="You don't have an open order."
            )
        
        if quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity must be greater than 0."
            )

        return await self.__admin_order_item_repository.update_order_item(admin_id, order_item_id, quantity, language=language)
