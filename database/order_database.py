import asyncpg
from datetime import datetime
from typing import List
from database.connection_string import connection_string
from models.admin_model import OrderBaseModel


class OrderDB:
    def __init__(self):
        self.connection_string = connection_string()

    async def get_orders_by_datetime(self, target_datetime: datetime, warehouse_id: int) -> List[OrderBaseModel]:

        start_time = target_datetime.replace(hour=0, minute=0, second=0, microsecond=0)

        print(warehouse_id)
        conn = None
        try:
            conn = await asyncpg.connect(self.connection_string)
            query = '''
            SELECT id, by, seller, status, updated_at, canceled_at, 
                   total_amount_with_discount, total_amount, warehouse_id, 
                   payment_type, created_at, user_name, user_phone, notes
            FROM admin_orders
            WHERE warehouse_id = $2 AND updated_at >= $1 AND updated_at < $1 + interval '1 day'
            ORDER BY updated_at
            '''
            orders = await conn.fetch(query, start_time, warehouse_id)
            return [OrderBaseModel(**dict(order)) for order in orders]
        except Exception as error:
            print(f"Error while fetching orders: {error}")
            return []
        finally:
            if conn:
                await conn.close()
