from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI

from database.connection_string import connection_string

pool = None

from asyncpg import create_pool


async def init_db():
    global pool
    pool = await create_pool(dsn=connection_string())


async def close_db():
    if pool is not None:
        await pool.close()
