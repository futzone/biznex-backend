from datetime import datetime

from database.init import pool
from models.admin_order_model import AdminOrderModel
from utils.time_utils import now_time


class AdminOrderDB:
    def __init__(self):
        self.pool = pool

    async def create_order(self, order: AdminOrderModel):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = """
                INSERT INTO orders (by, seller, status, updated_at, canceled_at, total_amount_with_discount, 
                                    total_amount, warehouse_id, payment_type, created_at, user_name, user_phone, notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING id;
                """
                return await conn.fetchval(
                    query, order.by, order.seller, order.status, now_time(), order.canceled_at,
                    order.total_amount_with_discount, order.total_amount, order.warehouse_id,
                    order.payment_type, now_time(), order.user_name, order.user_phone, order.notes
                )

    async def update_order(self, order_id: int, order: AdminOrderModel):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = """
                UPDATE orders
                SET by = $1, seller = $2, status = $3, updated_at = $4, canceled_at = $5, 
                    total_amount_with_discount = $6, total_amount = $7, warehouse_id = $8, 
                    payment_type = $9, user_name = $10, user_phone = $11, notes = $12
                WHERE id = $13;
                """
                await conn.execute(
                    query, order.by, order.seller, order.status, now_time(), order.canceled_at,
                    order.total_amount_with_discount, order.total_amount, order.warehouse_id,
                    order.payment_type, order.user_name, order.user_phone, order.notes, order_id
                )
                return {"message": "Order updated successfully"}

    async def delete_order(self, order_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = "DELETE FROM orders WHERE id = $1;"
                await conn.execute(query, order_id)
                return {"message": "Order deleted successfully"}

    async def get_order(self, order_id: int):
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM orders WHERE id = $1;"
            row = await conn.fetchrow(query, order_id)
            return AdminOrderModel(**dict(row)) if row else None

    async def get_warehouse_orders(self, warehouse_id: int):
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM orders WHERE warehouse_id = $1 ORDER BY created_at DESC;"
            rows = await conn.fetch(query, warehouse_id)
            return [AdminOrderModel(**dict(row)) for row in rows]

    async def get_by_seller(self, seller_id: int):
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM orders WHERE seller = $1 ORDER BY created_at DESC;"
            rows = await conn.fetch(query, seller_id)
            return [AdminOrderModel(**dict(row)) for row in rows]

    async def get_by_user(self, user_phone: str):
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM orders WHERE user_phone = $1 ORDER BY created_at DESC;"
            rows = await conn.fetch(query, user_phone)
            return [AdminOrderModel(**dict(row)) for row in rows]
