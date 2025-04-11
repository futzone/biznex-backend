from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import Depends, HTTPException
from sqlalchemy import Enum, and_, or_, DECIMAL
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.models.order import AdminOrder, AdminOrderItem
from app.api.models.product import Product, ProductVariant, Promotion, promotion_product_variants
from app.api.schemas.order import AdminOrderItemResponse, AdminOrderItemSchema, AdminOrderResponse, AdminProductVariantResponse, CompleteOrderRequest, AdminOrderUpdate
from app.core.databases.postgres import get_general_session
from app.core.models.enums import AdminOrderStatusEnum, PaymentMethodEnum
from utils.time_utils import now_time


class AdminOrderRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def get_admin_current_order(self, admin_id: int, language: str) -> AdminOrderResponse | None:
        result = await self.__session.execute(
            select(AdminOrder)
            .where(
                and_(
                    AdminOrder.by == admin_id,
                    AdminOrder.status == AdminOrderStatusEnum.opened
                )
            )
            .options(
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.product),
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.color),
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.size),
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.measure),
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.images),
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.promotions)
            )
        )

        opened_order = result.scalars().first()

        if not opened_order:
            return None

        return AdminOrderResponse(
            id=opened_order.id,
            by=opened_order.by,
            seller_id=opened_order.seller,
            status=opened_order.status,
            user_name=opened_order.user_name,
            user_phone=opened_order.user_phone,
            total_amount_with_discount=opened_order.total_amount_with_discount,
            total_amount=opened_order.total_amount,
            payment_type=opened_order.payment_type,
            notes=opened_order.notes,
            created_at=opened_order.created_at,
            updated_at=opened_order.updated_at,
            canceled_at=opened_order.canceled_at,
            product_variants=[
                AdminOrderItemResponse(
                    id=item.id,
                    order_id=item.order_id,
                    product_variant=AdminProductVariantResponse.from_variant(
                        item.product_variant,
                        language
                    ),
                    quantity=item.quantity,
                    price_per_unit=item.price_per_unit,
                    price_with_discount=item.price_with_discount,
                    total_amount_with_discount=item.total_amount_with_discount,
                    total_amount=item.total_amount,
                    notes=item.notes,
                    created_at=item.created_at,
                    updated_at=item.updated_at
                ) for item in opened_order.items
            ]
        )

    async def get_order_by_id(self, order_id: int, language: str) -> AdminOrderResponse | None:
        result = await self.__session.execute(
            select(AdminOrder)
            .where(
                AdminOrder.id == order_id,
            )
            .options(
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.product),
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.color),
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.size),
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.measure),
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.images),
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.promotions)
            )
        )

        opened_order = result.scalars().first()

        if not opened_order:
            return None

        return AdminOrderResponse(
            id=opened_order.id,
            by=opened_order.by,
            seller_id=opened_order.seller,
            status=opened_order.status,
            user_name=opened_order.user_name,
            user_phone=opened_order.user_phone,
            total_amount_with_discount=opened_order.total_amount_with_discount,
            total_amount=opened_order.total_amount,
            payment_type=opened_order.payment_type,
            notes=opened_order.notes,
            created_at=opened_order.created_at,
            updated_at=opened_order.updated_at,
            canceled_at=opened_order.canceled_at,
            product_variants=[
                AdminOrderItemResponse(
                    id=item.id,
                    order_id=item.order_id,
                    product_variant=AdminProductVariantResponse.from_variant(
                        item.product_variant,
                        language
                    ),
                    quantity=item.quantity,
                    price_per_unit=item.price_per_unit,
                    price_with_discount=item.price_with_discount,
                    total_amount_with_discount=item.total_amount_with_discount,
                    total_amount=item.total_amount,
                    notes=item.notes,
                    created_at=item.created_at,
                    updated_at=item.updated_at
                ) for item in opened_order.items
            ]
        )

    async def create_complete_order(self, admin_id: int, data: CompleteOrderRequest, warehouse_id: int, language: str):
        admin_order = AdminOrder(
            by=admin_id,
            seller=data.seller_id,
            status=AdminOrderStatusEnum.completed,
            user_name=data.user_name,
            user_phone=data.user_phone,
            warehouse_id=warehouse_id,
            created_at=data.created_at,
            payment_type=PaymentMethodEnum(data.payment_type),
        )

        self.__session.add(admin_order)
        await self.__session.commit()
        await self.__session.refresh(admin_order)

        total_amount = Decimal('0')
        total_discount_amount = Decimal('0')

        for item in data.items:
            product_variant = await self.__session.execute(
                select(ProductVariant)
                .join(Product)
                .where(and_(
                    ProductVariant.barcode == int(item.barcode),
                    Product.warehouse_id == warehouse_id
                ))
            )
            product_variant = product_variant.scalar_one_or_none()

            if not product_variant:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product variant not found for barcode {item.barcode}"
                )

            original_price = Decimal(str(item.custom_price or product_variant.current_price))

            active_promotion = await self.get_active_promotion(product_variant.id)
            discounted_price = original_price

            if active_promotion:
                discount_multiplier = Decimal(str((100 - active_promotion.discount) / 100))
                discounted_price = (original_price * discount_multiplier).quantize(Decimal('0.01'))

            item_quantity = Decimal(str(item.quantity))

            order_item = AdminOrderItem(
                order_id=admin_order.id,
                product_variant_id=product_variant.id,
                quantity=item.quantity,
                price_per_unit=original_price,
                price_with_discount=discounted_price,
                total_amount=original_price * item_quantity,
                total_amount_with_discount=discounted_price * item_quantity,
            )

            self.__session.add(order_item)

            total_amount += original_price * item_quantity
            total_discount_amount += discounted_price * item_quantity

        admin_order.total_amount = total_amount
        admin_order.total_amount_with_discount = total_discount_amount

        if data.status == "completed":
            for item_request in data.items:
                product_variant = await self.__session.execute(
                    select(ProductVariant)
                    .where(ProductVariant.barcode == int(item_request.barcode))
                )
                product_variant = product_variant.scalar_one_or_none()

                if product_variant:
                    if product_variant.amount < item_request.quantity:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Insufficient stock for product {product_variant.id} {product_variant.amount}"
                        )

                    product_variant.amount -= item_request.quantity
                    self.__session.add(product_variant)

        await self.__session.commit()
        await self.__session.refresh(admin_order)

        return {
            "id": admin_order.id,
            "by": admin_order.by,
            "seller": admin_order.seller,
            "status": admin_order.status,
            "user_name": admin_order.user_name,
            "user_phone": admin_order.user_phone,
            "total_amount": admin_order.total_amount,
            "total_amount_with_discount": admin_order.total_amount_with_discount,
            "payment_type": admin_order.payment_type,
            "notes": admin_order.notes,
            "created_at": admin_order.created_at,
            "updated_at": admin_order.updated_at,
        }

    async def create_new_order(self, admin_id: int, warehouse_id: int) -> AdminOrderResponse:
        admin_order = AdminOrder(by=admin_id, warehouse_id=warehouse_id)
        self.__session.add(admin_order)
        await self.__session.commit()

        await self.__session.refresh(admin_order)

        return AdminOrderResponse(
            id=admin_order.id,
            by=admin_order.by,
            seller_id=admin_order.seller,
            status=admin_order.status,
            user_name=admin_order.user_name,
            user_phone=admin_order.user_phone,
            total_amount=admin_order.total_amount,
            payment_type=admin_order.payment_type,
            notes=admin_order.notes,
            created_at=admin_order.created_at,
            updated_at=admin_order.updated_at,
            canceled_at=admin_order.canceled_at,
            product_variants=[]
        )

    async def update_status_order(self, admin_id: int, data: AdminOrderUpdate) -> dict:
        result = await self.__session.execute(
            select(AdminOrder)
            .where(
                and_(
                    AdminOrder.by == admin_id,
                    AdminOrder.status == AdminOrderStatusEnum.opened
                )
            )
            .options(selectinload(AdminOrder.product_variants))
        )

        admin_order = result.unique().scalars().first()

        if not admin_order:
            raise HTTPException(status_code=404, detail="Order not found")

        if data.status == AdminOrderStatusEnum.completed:
            for order_item in admin_order.product_variants:
                product_variant = await self.__session.get(ProductVariant, order_item.product_variant_id)
                if product_variant:
                    if product_variant.amount < order_item.quantity:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Insufficient stock for product '{product_variant.id}'"
                        )
                    product_variant.amount -= float(order_item.quantity)

        admin_order.status = AdminOrderStatusEnum(data.status)
        admin_order.seller = data.seller_id if data.seller_id else admin_order.seller
        admin_order.payment_type = PaymentMethodEnum(data.payment_type) if admin_order.payment_type else PaymentMethodEnum.cash
        admin_order.user_name = data.user_name if data.user_name else admin_order.user_name
        admin_order.user_phone = data.user_phone if data.user_phone else admin_order.user_phone
        admin_order.updated_at = now_time()
        # admin_order.warehouse_id =

        await self.__session.commit()
        return {
            "message": "Order closed successfully",
            "status": admin_order.status.value,
            "payment_method": admin_order.payment_type
        }

    async def get_all_closed_orders(self, admin_id: int, language: str, limit: int, offset: int) -> List[AdminOrderResponse] | None:
        result = await self.__session.execute(
            select(AdminOrder)
            .where(
                and_(
                    AdminOrder.by == admin_id,
                    or_(
                        AdminOrder.status == AdminOrderStatusEnum.completed,
                        AdminOrder.status == AdminOrderStatusEnum.cancelled
                    )
                )
            )
            .options(
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.product),
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.color),
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.size),
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.measure),
                selectinload(AdminOrder.items)
                .selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.images)
            )
            .order_by(AdminOrder.updated_at.desc())
            .limit(limit).offset(offset)
        )

        closed_orders = result.scalars().all()

        if not closed_orders:
            return []

        return [
            AdminOrderResponse(
                id=order.id,
                by=order.by,
                seller=order.seller,
                status=order.status,
                user_name=order.user_name,
                user_phone=order.user_phone,
                total_amount=order.total_amount,
                total_amount_with_discount=order.total_amount_with_discount,
                payment_type=order.payment_type,
                notes=order.notes,
                created_at=order.created_at,
                updated_at=order.updated_at,
                canceled_at=order.canceled_at,
                product_variants=[
                    AdminOrderItemResponse(
                        id=item.id,
                        order_id=item.order_id,
                        product_variant=AdminProductVariantResponse(
                            id=item.product_variant.id,
                            barcode=str(item.product_variant.barcode),
                            current_price=item.product_variant.current_price,
                            name=item.product_variant.product.name.get(language, ""),
                            main_image=item.product_variant.images[0].image if item.product_variant.images else "",
                            color=item.product_variant.color.name.get(language, "") if item.product_variant.color else "",
                            color_hex=item.product_variant.color.hex_code if item.product_variant.color else "",
                            size=item.product_variant.size.size if item.product_variant.size else "",
                            measure=item.product_variant.measure.name if item.product_variant.measure else "",
                            images=[img.image for img in item.product_variant.images] if item.product_variant.images else []  # Add this
                        ),
                        quantity=item.quantity,
                        price_per_unit=item.price_per_unit,
                        price_with_discount=item.price_with_discount,
                        payment_type=order.payment_type,
                        total_amount_with_discount=item.total_amount_with_discount,
                        total_amount=item.total_amount,
                        notes=item.notes,
                        created_at=item.created_at,
                        updated_at=item.updated_at
                    ) for item in order.items
                ]
            )
            for order in closed_orders
        ]

    async def get_active_promotion(self, product_variant_id: int) -> Optional[Promotion]:
        result = await self.__session.execute(
            select(Promotion)
            .join(promotion_product_variants)
            .where(
                and_(
                    promotion_product_variants.c.product_variant_id == product_variant_id,
                    Promotion.is_active == True,
                )
            )
            .order_by(Promotion.created_at.desc())
        )
        return result.scalar_one_or_none()
