from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import Depends, HTTPException
from sqlalchemy import and_, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api.models import ProductVariant, Product
from app.api.models.order import AdminOrder, AdminOrderItem
from app.api.models.product import Promotion, promotion_product_variants
from app.api.schemas.order import AdminOrderItemResponse, AdminOrderItemReturnSchema, AdminOrderUpdate, AdminProductVariantResponse, OrderItemRequest
from app.core.databases.postgres import get_general_session
from app.core.models.enums import AdminOrderStatusEnum, PaymentMethodEnum
from utils.time_utils import now_time


class AdminOrderItemRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def get_admin_order_items(self, admin_id: int, language: str) -> List[AdminOrderItemResponse]:
        order_result = await self.__session.execute(
            select(AdminOrder)
            .where(
                and_(
                    AdminOrder.by == admin_id,
                    AdminOrder.status == AdminOrderStatusEnum.opened
                )
            )
        )
        order = order_result.scalar_one_or_none()

        if not order:
            raise HTTPException(
                status_code=404,
                detail="No open orders found"
            )

        items_result = await self.__session.execute(
            select(AdminOrderItem)
            .options(
                selectinload(AdminOrderItem.product_variant).selectinload(ProductVariant.product),
                selectinload(AdminOrderItem.product_variant).selectinload(ProductVariant.color),
                selectinload(AdminOrderItem.product_variant).selectinload(ProductVariant.size),
                selectinload(AdminOrderItem.product_variant).selectinload(ProductVariant.measure),
                selectinload(AdminOrderItem.product_variant).selectinload(ProductVariant.images)
            )
            .where(AdminOrderItem.order_id == order.id)
        )
        items = items_result.scalars().all()

        response = []
        for item in items:
            product_variant = item.product_variant
            main_image = product_variant.images[0].image if product_variant.images else "default_image.jpg"

            response.append(AdminOrderItemResponse(
                id=item.id,
                order_id=order.id,
                product_variant=AdminProductVariantResponse(
                    id=product_variant.id,
                    name=product_variant.product.name.get(language, ""),
                    barcode=str(item.product_variant.barcode),
                    current_price=product_variant.current_price,
                    main_image=main_image,
                    color=product_variant.color.name.get(language, "") ,
                    color_hex=product_variant.color.hex_code if product_variant.color else "",
                    size=product_variant.size.size if product_variant.size else "",
                    measure=product_variant.measure.name if product_variant.measure else "",
                    images=[img.image for img in item.product_variant.images] if item.product_variant.images else []  
                ),
                quantity=item.quantity,
                price_per_unit=item.price_per_unit,
                price_with_discount=item.price_with_discount,
                total_amount_with_discount=item.total_amount_with_discount,
                total_amount=item.total_amount,
                payment_type=order.payment_type,
                notes=item.notes,
                created_at=item.created_at,
                updated_at=item.updated_at,
            ))
        
        return response

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

    async def add_items_to_order(
        self, 
        items: List[OrderItemRequest], 
        order_id: int, 
        language: str, 
        warehouse_id: int
    ) -> List[AdminOrderItemResponse]:
        order = await self.__session.execute(
            select(AdminOrder).where(
                and_(
                    AdminOrder.id == order_id,
                    AdminOrder.status == AdminOrderStatusEnum.opened
                )
            )
        )
        order = order.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Open order not found")
        
        responses = []
        
        if not isinstance(items, list):
            items = [items]
        
        for item_data in items:
            try:
                barcode = item_data.barcode
                quantity = item_data.quantity
                custom_price = item_data.custom_price
                
                product_variant = await self.__session.execute(
                    select(ProductVariant)
                    .join(Product)
                    .where(and_(
                        ProductVariant.barcode == int(barcode),
                        Product.warehouse_id == warehouse_id
                    ))
                    .options(
                        selectinload(ProductVariant.product),
                        selectinload(ProductVariant.color),
                        selectinload(ProductVariant.size),
                        selectinload(ProductVariant.measure),
                        selectinload(ProductVariant.images),
                        selectinload(ProductVariant.promotions),
                        selectinload(ProductVariant.product).selectinload(Product.subcategory)
                    )
                )
                product_variant = product_variant.scalar_one_or_none()
                
                if not product_variant:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Product variant with barcode {barcode} not found"
                    )
                
                active_promotion = await self.get_active_promotion(product_variant.id)
                original_price = Decimal(str(product_variant.current_price))
                discounted_price = original_price
                
                if custom_price is not None:
                    original_price = Decimal(str(custom_price))
                    discounted_price = original_price
                if active_promotion:
                    discount_multiplier = Decimal(str((100 - active_promotion.discount) / 100))
                    discounted_price = (original_price * discount_multiplier).quantize(Decimal('0.01'))
                
                existing_item = await self.__session.execute(
                    select(AdminOrderItem).where(
                        and_(
                            AdminOrderItem.order_id == order_id,
                            AdminOrderItem.product_variant_id == product_variant.id
                        )
                    )
                    .options(
                        selectinload(AdminOrderItem.product_variant)
                        .selectinload(ProductVariant.color),
                        selectinload(AdminOrderItem.product_variant)
                        .selectinload(ProductVariant.size),
                        selectinload(AdminOrderItem.product_variant)
                        .selectinload(ProductVariant.measure),
                        selectinload(AdminOrderItem.product_variant)
                        .selectinload(ProductVariant.images)
                    )
                )
                existing_item = existing_item.scalar_one_or_none()
                
                if existing_item:
                    existing_item.quantity += quantity
                    if custom_price is not None:
                        existing_item.price_per_unit = original_price
                        existing_item.price_with_discount = discounted_price
                    existing_item.total_amount = existing_item.calculate_total()
                    existing_item.price_with_discount = discounted_price
                    existing_item.total_amount_with_discount = existing_item.calculate_total_with_discount()
                    
                    order.total_amount += original_price * quantity
                    order.total_amount_with_discount += discounted_price * quantity
                    
                    item_response = existing_item
                else:
                    new_item = AdminOrderItem(
                        order_id=order_id,
                        product_variant_id=product_variant.id,
                        quantity=quantity,
                        price_per_unit=original_price,
                        price_with_discount=discounted_price,
                        total_amount=original_price * quantity,
                        total_amount_with_discount=discounted_price * quantity
                    )
                    
                    self.__session.add(new_item)
                    await self.__session.flush()
                    
                    new_item.product_variant = product_variant
                    
                    order.total_amount += original_price * quantity
                    order.total_amount_with_discount += discounted_price * quantity
                    
                    item_response = new_item

                if hasattr(item_response, 'product_variant') and item_response.product_variant:
                    response_item = AdminOrderItemResponse.from_order_item(item_response, language)
                    responses.append(response_item)
                else:
                    item_response.product_variant = product_variant
                    response_item = AdminOrderItemResponse.from_order_item(item_response, language)
                    responses.append(response_item)
                    
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to add item to order: {str(e)}"
                )
        await self.__session.commit()
        
        return responses

    async def return_order_item(
        self,
        order_item_id: int,
        data: AdminOrderItemReturnSchema
    ) -> AdminOrderItemResponse:
        query = (
            select(AdminOrderItem, ProductVariant, AdminOrder)
            .join(ProductVariant, AdminOrderItem.product_variant_id == ProductVariant.id)
            .join(AdminOrder, AdminOrderItem.order_id == AdminOrder.id)
            .where(
                and_(
                    AdminOrderItem.id == order_item_id,
                    AdminOrderItem.order_id == data.order_id,
                    AdminOrder.status == AdminOrderStatusEnum.completed
                )
            )
        )

        result = await self.__session.execute(query)
        row = result.first()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Order item not found or order is not in completed status"
            )

        order_item, product_variant, order = row

        if order_item.quantity < data.return_quantity:
            raise HTTPException(
                status_code=400,
                detail="Return quantity is greater than the ordered quantity"
            )

        try:
            new_amount = float(product_variant.amount) + float(data.return_quantity)
            await self.__session.execute(
                update(ProductVariant)
                .where(ProductVariant.id == product_variant.id)
                .values(amount=new_amount)
            )

            new_quantity = float(order_item.quantity) - data.return_quantity
            new_total_amount = new_quantity * float(order_item.price_per_unit)

            await self.__session.execute(
                update(AdminOrderItem)
                .where(AdminOrderItem.id == order_item_id)
                .values(
                    quantity=new_quantity,
                    total_amount=new_total_amount
                )
            )


            await self.__session.commit()
        except Exception as e:
            await self.__session.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to process return: " + str(e)
            )



        updated_variant = await self.__session.execute(
            select(ProductVariant)
            .where(ProductVariant.id == product_variant.id)
            .options(
                selectinload(ProductVariant.product),
                selectinload(ProductVariant.color),
                selectinload(ProductVariant.size),
                selectinload(ProductVariant.measure),
                selectinload(ProductVariant.images)
            )
        )
        updated_variant = updated_variant.scalar()

        return AdminOrderItemResponse(
            id=order_item.id,
            order_id=order_item.order_id,
            product_variant=AdminProductVariantResponse.from_variant(updated_variant),
            quantity=order_item.quantity,
            price_per_unit=order_item.price_per_unit,
            total_amount=order_item.total_amount,
            notes=order_item.notes,
            created_at=order_item.created_at,
            updated_at=order_item.updated_at
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
            .options(selectinload(AdminOrder.items))
        )
        
        admin_order = result.unique().scalars().first()
        
        if not admin_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if data.status == AdminOrderStatusEnum.completed:
            for order_item in admin_order.items:
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
        admin_order.payment_type = PaymentMethodEnum(data.payment_type) if data.payment_type else PaymentMethodEnum.cash
        admin_order.user_name = data.user_name if data.user_name else admin_order.user_name
        admin_order.user_phone = data.user_phone if data.user_phone else admin_order.user_phone
        
        admin_order.final_amount = admin_order.total_amount_with_discount if data.with_discount else admin_order.total_amount
        admin_order.updated_at = now_time()
        
        await self.__session.commit()
        return {
            "message": "Order closed successfully",
            "status": admin_order.status.value,
            "payment_method": admin_order.payment_type,
            "final_amount": float(admin_order.final_amount),
            "with_discount": data.with_discount
        }

    async def update_order_item(self, admin_id: int, order_item_id: int, quantity: float, language: str):
        query = (
            select(AdminOrder, AdminOrderItem)
            .join(AdminOrderItem, and_(
                AdminOrderItem.order_id == AdminOrder.id,
                AdminOrderItem.id == order_item_id
            ))
            .where(
                AdminOrder.by == admin_id,
            )
            .options(
                selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.product),
                selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.color),
                selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.size),
                selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.measure),
                selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.images)
            )
        )

        result = await self.__session.execute(query)
        row = result.first()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Order item not found or order is not in opened status"
            )

        order, item = row

        try:
            product_variant = item.product_variant
            new_amount = float(product_variant.amount) + float(item.quantity) - quantity

            await self.__session.execute(
                update(ProductVariant)
                .where(ProductVariant.id == product_variant.id)
                .values(amount=new_amount)
            )

            new_total = float(order.total_amount) - float(item.total_amount)
            new_total += float(product_variant.current_price) * quantity
            await self.__session.execute(
                update(AdminOrder)
                .where(AdminOrder.id == order.id)
                .values(total_amount=new_total)
            )

            await self.__session.execute(
                update(AdminOrderItem)
                .where(AdminOrderItem.id == order_item_id)
                .values(quantity=quantity)
            )

            await self.__session.commit()

            updated_item_query = (
                select(AdminOrderItem)
                .where(AdminOrderItem.id == order_item_id)
                .options(
                    selectinload(AdminOrderItem.product_variant)
                    .selectinload(ProductVariant.product),
                    selectinload(AdminOrderItem.product_variant)
                    .selectinload(ProductVariant.color),
                    selectinload(AdminOrderItem.product_variant)
                    .selectinload(ProductVariant.size),
                    selectinload(AdminOrderItem.product_variant)
                    .selectinload(ProductVariant.measure),
                    selectinload(AdminOrderItem.product_variant)
                    .selectinload(ProductVariant.images)
                )
            )
            updated_result = await self.__session.execute(updated_item_query)
            updated_item = updated_result.scalar_one_or_none()

            if not updated_item:
                raise HTTPException(status_code=500, detail="Failed to retrieve updated order item")

            return AdminOrderItemResponse.from_order_item(updated_item, language)

        except Exception as e:
            await self.__session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update order item: {str(e)}"
            )


    async def delete_order_item(self, admin_id: int, order_item_id: int):
        query = (
            select(AdminOrder, AdminOrderItem)
            .join(AdminOrderItem, and_(
                AdminOrderItem.order_id == AdminOrder.id,
                AdminOrderItem.id == order_item_id
            ))
            .where(
                and_(
                    AdminOrder.by == admin_id,
                    AdminOrder.status == AdminOrderStatusEnum.opened
                )
            )
            .options(
                selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.product),
                selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.color),
                selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.size),
                selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.measure),
                selectinload(AdminOrderItem.product_variant)
                .selectinload(ProductVariant.images)
            )
        )

        result = await self.__session.execute(query)
        row = result.first()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Order item not found or order is not in opened status"
            )

        order, item = row

        try:
            product_variant = item.product_variant
            new_amount = float(product_variant.amount) + float(item.quantity)

            await self.__session.execute(
                update(ProductVariant)
                .where(ProductVariant.id == product_variant.id)
                .values(amount=new_amount)
            )

            new_total = float(order.total_amount) - float(item.total_amount)
            await self.__session.execute(
                update(AdminOrder)
                .where(AdminOrder.id == order.id)
                .values(total_amount=new_total)
            )

            await self.__session.execute(
                delete(AdminOrderItem)
                .where(AdminOrderItem.id == order_item_id)
            )

            await self.__session.commit()
        except Exception as e:
            await self.__session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete order item: {str(e)}"
            )

        return None