from database.init import pool
from datetime import datetime

from models.admin_order_item_model import AdminOrderItemModel
from utils.time_utils import now_time


class AdminOrderItemDB:
    def __init__(self):
        self.pool = pool

    async def create_order_item(self, order_item: AdminOrderItemModel):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = """
                INSERT INTO order_items (order_id, product_variant_id, quantity, price_per_unit, total_amount, 
                                         total_amount_with_discount, price_with_discount, created_at, updated_at, notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id;
                """
                return await conn.fetchval(
                    query, order_item.order_id, order_item.product_variant_id, order_item.quantity,
                    order_item.price_per_unit, order_item.total_amount, order_item.total_amount_with_discount,
                    order_item.price_with_discount, now_time(), now_time(), order_item.notes
                )

    async def update_order_item(self, order_item_id: int, order_item: AdminOrderItemModel):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = """
                UPDATE order_items
                SET order_id = $1, product_variant_id = $2, quantity = $3, price_per_unit = $4, total_amount = $5, 
                    total_amount_with_discount = $6, price_with_discount = $7, updated_at = $8, notes = $9
                WHERE id = $10;
                """
                await conn.execute(
                    query, order_item.order_id, order_item.product_variant_id, order_item.quantity,
                    order_item.price_per_unit, order_item.total_amount, order_item.total_amount_with_discount,
                    order_item.price_with_discount, now_time(), order_item.notes, order_item_id
                )
                return {"message": "Order item updated successfully"}

    async def delete_order_item(self, order_item_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = "DELETE FROM order_items WHERE id = $1;"
                await conn.execute(query, order_item_id)
                return {"message": "Order item deleted successfully"}

    async def get_order_item(self, order_item_id: int):
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM order_items WHERE id = $1;"
            row = await conn.fetchrow(query, order_item_id)
            return AdminOrderItemModel(**dict(row)) if row else None

    async def get_order_items(self, order_id: int):
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM order_items WHERE order_id = $1 ORDER BY created_at DESC;"
            rows = await conn.fetch(query, order_id)
            return [AdminOrderItemModel(**dict(row)) for row in rows]
