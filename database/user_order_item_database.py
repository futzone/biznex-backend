from datetime import datetime
from models.user_order_model import UserOrderItem


class UserOrderItemDB:
    def __init__(self, pool):
        self.pool = pool

    async def init_table(self):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = """
                    CREATE TABLE IF NOT EXISTS order_items (
                        id SERIAL PRIMARY KEY,
                        order_id INT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                        product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                        quantity INT NOT NULL,
                        total_amount FLOAT NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT now(),
                        updated_at TIMESTAMPTZ DEFAULT now()
                    );
                    """
                await conn.execute(query)

    async def create_order_item(self, item: UserOrderItem):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = """
                INSERT INTO order_items (order_id, product_id, quantity, total_amount, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id;
                """
                return await conn.fetchval(
                    query, item.order_id, item.product_id, item.quantity, item.total_amount,
                    datetime.utcnow(), datetime.utcnow()
                )

    async def update_order_item(self, item_id: int, item: UserOrderItem):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = """
                UPDATE order_items
                SET order_id = $1, product_id = $2, quantity = $3, total_amount = $4, updated_at = $5
                WHERE id = $6;
                """
                await conn.execute(
                    query, item.order_id, item.product_id, item.quantity, item.total_amount,
                    datetime.utcnow(), item_id
                )
                return {"message": "Order item updated successfully"}

    async def delete_order_item(self, item_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = "DELETE FROM order_items WHERE id = $1;"
                await conn.execute(query, item_id)
                return {"message": "Order item deleted successfully"}

    async def get_order_item(self, item_id: int):
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM order_items WHERE id = $1;"
            row = await conn.fetchrow(query, item_id)
            return UserOrderItem(**dict(row)) if row else None

    async def get_order_items(self, order_id: int):
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM order_items WHERE order_id = $1;"
            rows = await conn.fetch(query, order_id)
            return [UserOrderItem(**dict(row)) for row in rows]
