import os
import logging
from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles
import socketio
from app.api.routers.chat import register_chat_handlers
from app.api.utils.backup_database import backup_database
from app.core.settings import get_settings, Settings
from starlette.middleware.cors import CORSMiddleware
from app.api.routers.role import router as role_router
from app.api.routers.warehouse import router as warehouse_router
from app.api.routers.product.category import router as category_router
from app.api.routers.product.subcategory import router as subcategory_router
from app.api.routers.product.product_information import router as product_information_router
from app.api.routers.product.rating import router as rating_router
from app.api.routers.product.rating_picture import router as rating_picture_router
from app.api.routers.product.wishlist import router as wishlist_router
from app.api.routers.product.size import router as size_router
from app.api.routers.product.color import router as color_router
from app.api.routers.product.measure import router as measure_router
from app.api.routers.product.product import router as product_router
from app.api.routers.product.promotion import router as promotion_router
from app.api.routers.product.product_image import router as product_image_router
from app.api.routers.user import router as user_router
from app.api.routers.admin import router as admin_router
from app.api.routers.admin_order import router as admin_order_router
from app.api.routers.admin_orderitem import router as admin_orderitem_router
from app.api.routers.revision import router as revision_router
from app.api.routers.product.banner import router as banner_router
from app.api.routers.auth import router as auth_router
from app.api.routers.order import router as order_router
from app.api.routers.orderitem import router as order_item_router
from app.api.routers.report import router as report_router
from app.api.routers.file import router as file_router
from app.api.routers.chat import router as chat_router
from app.api.routers.notification.notification import router as notification_router
from app.api.routers.device.device import router as device_router
from app.api.routers.utils import router as utils_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncpg

from database.connection_string import connection_string

settings: Settings = get_settings()
scheduler = AsyncIOScheduler()


async def set_timezone():
    conn = await asyncpg.connect(connection_string())
    await conn.execute("SET TIME ZONE 'Asia/Tashkent'")
    await conn.close()
    print('timezone set: Asia/Tashkent')


async def start_scheduler():
    print("Schuler started")
    await backup_database()
    scheduler.add_job(backup_database, 'interval', minutes=3600)
    scheduler.start()


def create_app() -> CORSMiddleware:
    logging.basicConfig(level=logging.INFO)
    app = FastAPI(
        docs_url="/MTFTc0t2czE5WUpLTnJGK21Qd00vajVrb3g0NWRTUTA5a2MwVTVnVzkydVUrOWVnWnlxbjlZK1YwL0tUU3VTMw/docs",
        title=settings.PROJECT_NAME + " API",
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION,

    )
    sio = socketio.AsyncServer(
        async_mode='asgi',
        cors_allowed_origins='*',
        logger=True,
        engineio_logger=True
    )

    app.mount("/socket.io", socketio.ASGIApp(sio))

    @app.on_event("startup")
    async def startup_event():
        await register_chat_handlers(sio, app)
        await start_scheduler()
        await set_timezone()

    os.makedirs("media/category", exist_ok=True)
    os.makedirs("media/profile_picture", exist_ok=True)
    os.makedirs("media/product_image", exist_ok=True)
    os.makedirs("media/rating", exist_ok=True)
    os.makedirs("media/warehouse", exist_ok=True)
    app.mount("/media", StaticFiles(directory="media"), name="media")

    v1_router = APIRouter(prefix=settings.API_V1_STR)

    v1_router.include_router(
        user_router, prefix="/user", tags=["User"]
    )
    v1_router.include_router(
        chat_router, prefix="/chat", tags=["Chat"]
    )
    v1_router.include_router(
        auth_router, prefix="/auth", tags=["Auth"]
    )
    v1_router.include_router(
        admin_router, prefix="/admin", tags=["Admin"]
    )
    v1_router.include_router(
        admin_order_router, prefix="/admin-order", tags=["Admin Order"]
    )
    v1_router.include_router(
        admin_orderitem_router, prefix="/admin-orderitem", tags=["Admin Order Item"]
    )
    v1_router.include_router(
        revision_router, prefix="/revision", tags=["Revision"]
    )
    v1_router.include_router(
        banner_router, prefix="/banner", tags=["Banner"]
    )
    v1_router.include_router(
        role_router, prefix="/role", tags=["Role"]
    )
    v1_router.include_router(
        warehouse_router, prefix="/warehouse", tags=["Warehouse"]
    )
    v1_router.include_router(
        category_router, prefix="/category", tags=["Category"])
    v1_router.include_router(
        subcategory_router, prefix="/subcategory", tags=["Subcategory"]
    )
    v1_router.include_router(
        product_information_router, prefix="/product-information", tags=["Product Information"]
    )
    v1_router.include_router(
        product_router, prefix="/product", tags=["Product"]
    )
    v1_router.include_router(
        promotion_router, prefix="/promotion", tags=["Promotion"]
    )
    v1_router.include_router(
        rating_router, prefix="/rating", tags=["Rating"]
    )
    v1_router.include_router(
        rating_picture_router, prefix="/rating-picture", tags=["Rating Picture"]
    )
    v1_router.include_router(
        wishlist_router, prefix="/wishlist", tags=["Wishlist"]
    )
    v1_router.include_router(
        size_router, prefix="/size", tags=["Size"]
    )
    v1_router.include_router(
        color_router, prefix="/color", tags=["Color"]
    )
    v1_router.include_router(
        measure_router, prefix="/measure", tags=["Measure"]
    )
    v1_router.include_router(
        product_image_router, prefix="/product-image", tags=["Product Image"]
    )
    v1_router.include_router(
        order_router, prefix="/order", tags=["Order"]
    )
    v1_router.include_router(
        order_item_router, prefix="/order-item", tags=["Order Item"]
    )
    v1_router.include_router(
        report_router, prefix="/report", tags=["Report"]
    )
    v1_router.include_router(
        utils_router, prefix="/utils", tags=["Utils"]
    )
    v1_router.include_router(
        notification_router, prefix="/notification", tags=["Notification"]
    )
    v1_router.include_router(
        device_router, prefix="/device", tags=["Device"]
    )
    v1_router.include_router(
        file_router, prefix="/file", tags=["File"]
    )

    app.include_router(v1_router)

    # app.add_event_handler("startup", start_scheduler)

    return CORSMiddleware(
        app,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
