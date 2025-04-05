import asyncpg
from fastapi import Depends
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.controllers.user import UserController
from constants.response_messages import ResponseMessages
from database.init import get_postgres
from database.product_variants_database import ProductVariantsDB
from database.user_order_database import UserOrderDB
from database.user_order_item_database import UserOrderItemDB
from models.pagination_model import PaginationModel
from models.user_order_model import UserOrderModel, UserOrder
from utils.current_user import current_user


class OrderApiRouter:
    @staticmethod
    async def create_order(
            request: Request, model: UserOrderModel,
            controller: UserController = Depends(),
            pool: asyncpg.Pool = Depends(get_postgres)
    ):
        if len(model.items) == 0:
            return JSONResponse(content={"detail": ResponseMessages.items_must_be_not_empty}, status_code=400)

        variant_db = ProductVariantsDB(pool=pool)
        total_amount = 0.0
        for item in model.items:
            variant = await variant_db.get_variant(variant_id=item.product_id)
            if variant is None:
                raise HTTPException(status_code=404, detail=ResponseMessages.product_not_found)

            if variant.amount < item.quantity:
                raise HTTPException(status_code=401, detail=ResponseMessages.amount_is_not_enough)

            total_amount += (item.quantity * variant.current_price)
            item.total_amount = item.quantity * variant.current_price

        user = await current_user(request=request, controller=controller)
        order_db = UserOrderDB(pool=pool)

        order = UserOrder(
            user_id=user.id,
            status=model.status,
            type=model.type,
            total_amount=model.total_amount if model.total_amount is not None else total_amount
        )

        order_id = await order_db.create_order(order)

        order_item_db = UserOrderItemDB(pool=pool)
        for item in model.items:
            item.order_id = order_id
            await order_item_db.create_order_item(item=item)

        return JSONResponse(content={"detail": ResponseMessages.order_created}, status_code=201)

    @staticmethod
    async def get_user_orders(
            request: Request, model: PaginationModel,
            controller: UserController = Depends(),
            pool: asyncpg.Pool = Depends(get_postgres)
    ):
        print(model.dict())
        user = await current_user(request=request, controller=controller)
        print("user done")
        order_db = UserOrderDB(pool=pool)
        orders = await order_db.get_user_orders(user_id=user.id, status=model.status, limit=model.limit, offset=model.offset)
        print("orders done")
        order_item_db = UserOrderItemDB(pool=pool)
        variant_db = ProductVariantsDB(pool=pool)

        response_list = []
        for order in orders:
            print("order type: ", type(order))
            items_list = []
            items = await order_item_db.get_order_items(order_id=order.id)
            for item in items:
                print("order item type: ", type(item))
                variant = await variant_db.get_variant(variant_id=item.product_id)
                item_map = item.to_map()
                print("order item type: ", type(variant))
                item_map['variant'] = variant.to_map()
                items_list.append(item_map)

            order_map = order.to_map()
            order_map['items'] = items_list
            response_list.append(order_map)

        return JSONResponse(content=response_list, status_code=200)
