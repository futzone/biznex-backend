from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.order import OrderItemCreate, OrderItem
from app.api.repositories.orderitem import OrderItemRepository


class OrderItemController:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = OrderItemRepository(db)

    async def create_order_item(
        self,
        order_item_create: OrderItemCreate,
    ) -> OrderItem:
        return await self.repository.create(order_item_create)

    async def get_order_item(self, order_item_id: int) -> OrderItem:
        return await self.repository.get_by_id(order_item_id)

    async def update_order_item(
        self, order_item_id: int, order_item_update: OrderItemCreate
    ) -> OrderItem:
        return await self.repository.update(order_item_id, order_item_update)

    async def delete_order_item(self, order_item_id: int) -> bool:
        return await self.repository.delete(order_item_id)

    async def get_all_order_items(self, order_id: int) -> list[OrderItem]:
        return await self.repository.get_all_by_order_id(order_id)
