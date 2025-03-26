import asyncpg

from app.core.settings import get_settings
from database.user_order_database import UserOrderDB
from database.user_order_item_database import UserOrderItemDB


async def initialize_tables(pool_c: asyncpg.Pool):
    await UserOrderDB(pool=pool_c).init_table()
    await UserOrderItemDB(pool=pool_c).init_table()


settings = get_settings()
pool = None


async def init_db():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DATABASE,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT
        )
        print("✅ Database pool muvaffaqiyatli yaratildi.")


import asyncpg
import dotenv
from typing import Optional

dotenv.load_dotenv()

conn_pool: Optional[asyncpg.Pool] = None


async def init_postgres() -> None:
    global conn_pool
    try:
        conn_pool = await asyncpg.create_pool(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DATABASE,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            min_size=1, max_size=10,
        )

        if conn_pool is not None:
            await initialize_tables(conn_pool)
    except Exception as e:
        raise e


def get_postgres() -> asyncpg.Pool:
    global conn_pool
    if conn_pool is None:
        raise ConnectionError("PostgreSQL connection pool is not initialized.")
    try:
        return conn_pool
    except Exception as e:
        raise


async def close_postgres() -> None:
    global conn_pool
    if conn_pool is not None:
        try:
            await conn_pool.close()
        except Exception as e:
            raise e
