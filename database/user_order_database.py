from datetime import datetime
from typing import Optional

from models.user_order_model import UserOrder


class UserOrderDB:
    def __init__(self, pool):
        self.pool = pool

    async def init_table(self):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = """
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    status TEXT NOT NULL,
                    type TEXT NOT NULL,
                    total_amount FLOAT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    updated_at TIMESTAMPTZ DEFAULT now(),
                    canceled_at TIMESTAMPTZ
                );
                """
                await conn.execute(query)
                print('initialized: user order db')

    async def create_order(self, order: UserOrder):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = """
                INSERT INTO orders (user_id, status, type, total_amount, created_at, updated_at, canceled_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id;
                """
                return await conn.fetchval(
                    query, order.user_id, order.status, order.type, order.total_amount,
                    datetime.utcnow(), datetime.utcnow(), order.canceled_at
                )

    async def update_order(self, order_id: int, order: UserOrder):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = """
                UPDATE orders
                SET user_id = $1, status = $2, type = $3, total_amount = $4, updated_at = $5, canceled_at = $6
                WHERE id = $7;
                """
                await conn.execute(
                    query, order.user_id, order.status, order.type, order.total_amount,
                    datetime.utcnow(), order.canceled_at, order_id
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
            return UserOrder(**dict(row)) if row else None

    async def get_user_orders(self, user_id: int, status: Optional[str] = None, limit: int = 10, offset: int = 0):
        async with self.pool.acquire() as conn:
            if status is not None:
                query = """
                SELECT * FROM orders 
                WHERE user_id = $1 AND status = $2 
                ORDER BY created_at DESC 
                LIMIT $3 OFFSET $4;
                """
                params = [user_id, status, limit, offset]
            else:
                query = """
                SELECT * FROM orders 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT $2 OFFSET $3;
                """
                params = [user_id, limit, offset]

            rows = await conn.fetch(query, *params)
            return [UserOrder(**dict(row)) for row in rows]

    async def get_warehouse_orders(self, status: Optional[str] = None, limit: int = 10, offset: int = 0):
        async with self.pool.acquire() as conn:
            if status is not None:
                query = """
                SELECT * FROM orders 
                WHERE status = $1 
                ORDER BY created_at DESC 
                LIMIT $2 OFFSET $3;
                """
                params = [status, limit, offset]
            else:
                query = """
                SELECT * FROM orders 
                ORDER BY created_at DESC 
                LIMIT $1 OFFSET $2;
                """
                params = [limit, offset]

            rows = await conn.fetch(query, *params)
            return [UserOrder(**dict(row)) for row in rows]
