import asyncio
from datetime import datetime

from sqlalchemy import Integer, Text, Tuple, case, cast, distinct, func, and_, extract, or_

from typing import List, Optional, Sequence
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload

from app.api.constants.languages import languages
from app.api.models.order import AdminOrder, AdminOrderItem
from app.api.schemas.product.color import ColorCreateSchema, ColorResponseSchema, ColorLanguageResponseSchema
from app.api.schemas.product.size import SizeCreateSchema, SizeResponseSchema, SizeLanguageResponseSchema
from app.api.utils.translator import translate_text
from app.core.databases.postgres import get_general_session
from app.api.models.product import Color, Measure, Product, ProductVariant, Size, Subcategory, ProductImage
from app.api.schemas.product.product import (
    ProductFilterSchema,
    ProductListResponse,
    ProductResponseSchema,
    ProductCreateSchema,
    MainProductResponseSchema,
    ProductUpdateSchema,
    ProductVariantSalesResponse,
    ProductVariantSchema,
    ProductLanguageResponseSchema,
    MainProductLanguageResponseSchema,
)
from app.core.models.enums import AdminOrderStatusEnum, PaymentMethodEnum


class ProductRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.session = session

    async def get_product_by_id(self, product_id: int, language: str | None = None):
        result = await self.session.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(
                joinedload(Product.product_information),
                joinedload(Product.warehouse),
                joinedload(Product.subcategory),
                joinedload(Product.variants).joinedload(ProductVariant.color),
                joinedload(Product.variants).joinedload(ProductVariant.size),
                joinedload(Product.variants).joinedload(
                    ProductVariant.measure),
                joinedload(Product.variants).joinedload(ProductVariant.images),
                joinedload(Product.ratings),
            )
        )
        product = result.unique().scalar_one_or_none()
        if not product:
            return None
        return self._build_product_responsee(product, language)

    async def get_all_products(
            self, warehouse_id: int, language: str | None = None
    ):
        result = await self.session.execute(
            select(Product)
            .options(
                selectinload(Product.variants).selectinload(ProductVariant.images),
                selectinload(Product.ratings),
                selectinload(Product.variants).selectinload(ProductVariant.color),
                selectinload(Product.variants).selectinload(ProductVariant.size),
                selectinload(Product.subcategory),
            )
            .where(Product.warehouse_id == warehouse_id)
        )
        products = result.scalars().all()
        return [await self._build_product_response(product, language) for product in products]

    async def get_little_products_left(
        self, warehouse_id: int, limit: int, offset: int, language: str | None, amount: int = 10
    ) -> List[ProductResponseSchema | ProductLanguageResponseSchema]:
        result = await self.session.execute(
            select(Product)
            .options(
                selectinload(Product.variants).selectinload(ProductVariant.images),
                selectinload(Product.ratings),
                selectinload(Product.variants).selectinload(ProductVariant.color),
                selectinload(Product.variants).selectinload(ProductVariant.size),
                selectinload(Product.subcategory),
            )
            .join(Product.variants)
            .where(
                and_(
                    Product.warehouse_id == warehouse_id,
                    ProductVariant.amount > amount
                )
            )
            .limit(limit)
            .offset(offset)
        )
        products = result.scalars().all()
        return [await self._build_product_response(product, language) for product in products]

    async def get_product_variant_sales(
        self,
        language: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        warehouse_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProductVariantSalesResponse]:
        query = select(
            ProductVariant.id,
            ProductVariant.barcode,
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Color.hex_code.label("hex_code"), 
            Size.size.label("size"),      
            Measure.name.label("measure"),
            func.sum(AdminOrderItem.quantity).label("total_quantity_sold"),
            func.sum(AdminOrderItem.total_amount).label("total_amount_sold"),
            func.count(distinct(AdminOrderItem.order_id)).label("order_count")
        ).join(
            AdminOrderItem, ProductVariant.id == AdminOrderItem.product_variant_id
        ).join(
            AdminOrder, AdminOrder.id == AdminOrderItem.order_id
        ).join(
            Product, Product.id == ProductVariant.product_id
        ).outerjoin(
            Color, ProductVariant.color_id == Color.id
        ).outerjoin(
            Size, ProductVariant.size_id == Size.id
        ).join(
            Measure, ProductVariant.measure_id == Measure.id
        )
        filters = []
        
        filters.append(AdminOrder.status == AdminOrderStatusEnum.completed)

        if start_date:
            filters.append(AdminOrder.created_at >= start_date)
        if end_date:
            filters.append(AdminOrder.created_at <= end_date)
        
        if warehouse_id:
            filters.append(AdminOrder.warehouse_id == warehouse_id)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.group_by(
            ProductVariant.id,
            ProductVariant.barcode,
            Product.id,
            Product.name,
            Color.hex_code,
            Size.size,
            Measure.name
        ).order_by(func.sum(AdminOrderItem.quantity).desc())
        
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        rows = result.all()
        
        if not rows:
            return []
        
        sales_data = []
        for row in rows:
            product_name = row.product_name.get(language, "") if row.product_name else ""
                       
            sales_data.append(
                ProductVariantSalesResponse(
                    variant_id=row.id,
                    barcode=str(row.barcode),
                    product_id=row.product_id,
                    product_name=product_name,
                    color=row.hex_code if row.hex_code else "",
                    size=row.size if row.size else "",
                    measure=row.measure,
                    total_quantity_sold=float(row.total_quantity_sold),
                    total_amount_sold=float(row.total_amount_sold),
                    order_count=row.order_count
                )
            )
        
        return sales_data

    async def search_products(
        self,
        filters: ProductFilterSchema,
        language: str = 'uz',
        limit: int = 10,
        offset: int = 0,
        similarity_threshold: float = 0.1
    ) -> tuple[list[ProductResponseSchema], int]:
        stmt = (
            select(Product)
            .options(
                selectinload(Product.variants).selectinload(ProductVariant.images),
                selectinload(Product.ratings),
                selectinload(Product.variants).selectinload(ProductVariant.color),
                selectinload(Product.variants).selectinload(ProductVariant.size),
                selectinload(Product.subcategory)
            )
        )

        conditions = self._build_conditions(filters, language, similarity_threshold)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = self._apply_sorting(stmt, filters.sort_by, filters.sort_order)

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        products = result.scalars().unique().all()

        total = await self._get_total_count(conditions)

        return [await self._build_short_response(prod, language) for prod in products], total

    def _build_conditions(self, filters, language, threshold):
        conditions = []

        if filters.query:
            name_field = func.coalesce(Product.name[language].astext, "")
            desc_field = func.coalesce(Product.description[language].astext, "")
            conditions.append(or_(
                func.similarity(name_field, filters.query) > threshold,
                func.similarity(desc_field, filters.query) > threshold
            ))

        if filters.category_id:
            conditions.append(Product.subcategory.has(Subcategory.category_id == filters.category_id))
        if filters.subcategory_id:
            conditions.append(Product.subcategory_id == filters.subcategory_id)

        if filters.color_id:
            conditions.append(
                Product.variants.any(
                    ProductVariant.color_id.in_(
                        [int(cid) for cid in filters.color_id] 
                    )
                )
            )

        # Fix size_id filter
        if filters.size_id:
            conditions.append(
                Product.variants.any(
                    ProductVariant.size_id.in_(
                        [int(sid) for sid in filters.size_id] 
                    )
                )
            )
            
        if filters.min_price is not None:
            conditions.append(Product.variants.any(ProductVariant.current_price >= filters.min_price))
        if filters.max_price is not None:
            conditions.append(Product.variants.any(ProductVariant.current_price <= filters.max_price))

        if filters.has_discount:
            conditions.append(Product.variants.any(ProductVariant.discount > 0))
        if filters.min_discount is not None:
            conditions.append(Product.variants.any(ProductVariant.discount >= filters.min_discount))
        if filters.max_discount is not None:
            conditions.append(Product.variants.any(ProductVariant.discount <= filters.max_discount))

        if filters.in_stock is not None:
            conditions.append(
                Product.variants.any(ProductVariant.amount > 0)
                if filters.in_stock
                else Product.variants.any(ProductVariant.amount == 0)
            )

        if filters.measure_id:
            conditions.append(Product.measure_id == filters.measure_id)

        return conditions

    def _apply_sorting(self, stmt, sort_by, sort_order):
        if sort_by in ['price', 'discount']:
            subq = (
                select(
                    ProductVariant.product_id,
                    func.min(ProductVariant.current_price).label('min_price'),
                    func.max(ProductVariant.discount).label('max_discount')
                )
                .group_by(ProductVariant.product_id)
                .subquery()
            )
            
            stmt = stmt.join(subq, Product.id == subq.c.product_id, isouter=True)
            
            sort_field = {
                'price': subq.c.min_price,
                'discount': subq.c.max_discount
            }[sort_by]
        else:
            sort_field = {
                'created_at': Product.created_at,
            }.get(sort_by, Product.created_at)

        return stmt.order_by(sort_field.desc() if sort_order == 'desc' else sort_field.asc())

    async def _get_total_count(self, conditions):
        count_query = select(func.count(Product.id.distinct()))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        result = await self.session.execute(count_query)
        return result.scalar()

    async def _build_short_response(self, product: Product, language: str) -> ProductResponseSchema:
        main_variant = next(
            (v for v in product.variants if v.is_main),
            product.variants[0] if product.variants else None
        )

        total_stock = sum(v.amount for v in product.variants)
        color_codes = list(set(v.color.hex_code for v in product.variants if v.color))
        sizes = list(set(v.size.size for v in product.variants if v.size))

        return ProductResponseSchema(
            id=product.id,
            rating=self._calculate_rating(product.ratings),
            current_price=main_variant.current_price if main_variant else 0,
            old_price=main_variant.old_price if main_variant else 0,
            main_image=main_variant.images[0].image if main_variant and main_variant.images else None,
            name=product.name.get(language, ""),
            description=product.description.get(language, ""),
            product_information_id=product.product_information_id,
            warehouse_id=product.warehouse_id,
            subcategory_id=product.subcategory_id,
            subcategory_name=product.subcategory.name.get(language, "") if product.subcategory else "",
            total_stock=total_stock,
            color_code=color_codes,
            size=sizes
        )

    def _calculate_rating(self, ratings: list) -> Optional[float]:
        if not ratings:
            return None
        return sum(r.rating for r in ratings) / len(ratings)

    def _build_product_responsee(
            self, product: Product, language: str | None
    ) -> MainProductResponseSchema | MainProductLanguageResponseSchema:
        ratings = [r.rating for r in product.ratings] if product.ratings else []
        average_rating = sum(ratings) / len(ratings) if ratings else None

        color_codes = set()
        sizes = set()
        total_stock = 0
        variants = []

        if product.variants:
            for variant in product.variants:
                if variant.color and variant.color.hex_code:
                    color_codes.add(variant.color.hex_code)
                if variant.size and variant.size.size:
                    sizes.add(variant.size.size)

                total_stock += variant.amount

                if language is not None:
                    color = ColorResponseSchema(
                        id=variant.color.id if variant.color else None,
                        name=variant.color.name.get(language) if variant.color else None,
                        hex_code=variant.color.hex_code if variant.color else None,
                    ) if variant.color else None
                    
                    size = SizeResponseSchema(
                        id=variant.size.id if variant.size else None,
                        size=variant.size.size if variant.size else None,
                        description=variant.size.description.get(language) if variant.size and variant.size.description else '',
                        warehouse_id=variant.size.warehouse_id if variant.size else None
                    ) if variant.size else None
                else:
                    color = ColorLanguageResponseSchema.model_validate(variant.color) if variant.color else None
                    size = SizeLanguageResponseSchema.model_validate(variant.size) if variant.size else None
                    

                variant_data = {
                    "id": variant.id,
                    "barcode": variant.barcode,
                    "come_in_price": variant.come_in_price,
                    "current_price": variant.current_price,
                    "old_price": variant.old_price,
                    "discount": variant.discount,
                    "is_main": variant.is_main,
                    "amount": variant.amount,
                    "color": color,
                    "size": size,
                    "measure": variant.measure.name,
                    "images": [img.image for img in variant.images] if variant.images else [],
                }
                variants.append(ProductVariantSchema(**variant_data))

        if language is not None:
            return MainProductResponseSchema(
                id=product.id,
                rating=average_rating,
                name=product.name.get(language),
                description=product.description.get(language),
                product_information_id=product.product_information_id,
                warehouse_id=product.warehouse_id,
                product_information=(
                    {
                        "id": product.product_information.id,
                        "product_type": product.product_information.product_type,
                        "brand": product.product_information.brand,
                        "model_name": product.product_information.model_name,
                        "description": product.product_information.description.get(language),
                        "attributes": product.product_information.attributes,
                    }
                    if product.product_information
                    else {}
                ),
                warehouse=product.warehouse.name if product.warehouse else "",
                subcategory=product.subcategory.name.get(language) if product.subcategory else "",
                variants=variants,
                subcategory_name=product.subcategory.name.get(language) if product.subcategory else "",
                subcategory_id=product.subcategory_id,
                total_stock=total_stock,
                color_code=list(color_codes),
                size=list(sizes),
            )
        else:
            return MainProductLanguageResponseSchema(
                id=product.id,
                rating=average_rating,
                name=product.name,
                description=product.description,
                product_information_id=product.product_information_id,
                warehouse_id=product.warehouse_id,
                subcategory_id=product.subcategory_id,
                subcategory=product.subcategory.name if product.subcategory else {},
                product_information=(
                    {
                        "id": product.product_information.id,
                        "product_type": product.product_information.product_type,
                        "brand": product.product_information.brand,
                        "model_name": product.product_information.model_name,
                        "description": product.product_information.description,
                        "attributes": product.product_information.attributes,
                    }
                    if product.product_information
                    else {}
                ),
                warehouse=product.warehouse.name if product.warehouse else "",
                variants=variants,
                subcategory_name=product.subcategory.name.get(language, "") if product.subcategory else "",
                total_stock=total_stock,
                color_code=list(color_codes),
                size=list(sizes),
            )

    async def get_recomended_products(
        self, subcategory_id: int, limit: int, offset: int, language: str
    ) -> Sequence[ProductResponseSchema]:
        result = await self.session.execute(
            select(Product)
            .where(Product.subcategory_id == subcategory_id)
            .order_by(func.random())
            .options(
                selectinload(Product.variants).selectinload(ProductVariant.images),
                selectinload(Product.ratings),
                selectinload(Product.variants).selectinload(ProductVariant.color),
                selectinload(Product.variants).selectinload(ProductVariant.size),
                selectinload(Product.subcategory) 
            )
            .limit(limit)
            .offset(offset)
        )
        products = result.scalars().all()
        return [await self._build_product_response(prod, language) for prod in products]

    async def get_products(
        self, limit: int, offset: int, language: str | None
    ) -> list[ProductResponseSchema] | ProductLanguageResponseSchema:
        result = await self.session.execute(
            select(Product)
            .options(
                selectinload(Product.variants).selectinload(ProductVariant.images),
                selectinload(Product.ratings),
                selectinload(Product.variants).selectinload(ProductVariant.color),
                selectinload(Product.variants).selectinload(ProductVariant.size),
                selectinload(Product.subcategory),
            )
            .order_by(Product.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        products = result.scalars().all()

        responses = []
        for product in products:
            response = await self._build_product_response(product, language)
            responses.append(response)
        
        return responses

    async def get_products_by_warehouse_id(
        self, limit: int, offset: int, warehouse_id: int, language: str | None
    ) -> list[ProductResponseSchema] | ProductLanguageResponseSchema:
        result = await self.session.execute(
            select(Product)
            .where(Product.warehouse_id == warehouse_id)
            .options(
                selectinload(Product.variants).selectinload(ProductVariant.images),
                selectinload(Product.ratings),
                selectinload(Product.variants).selectinload(ProductVariant.color),
                selectinload(Product.variants).selectinload(ProductVariant.size),
                selectinload(Product.subcategory),
            )
            .order_by(Product.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        products = result.scalars().all()
        
        responses = []
        for product in products:
            response = await self._build_product_response(product, language)
            responses.append(response)
        
        return responses

    async def _build_product_response(
        self, product: Product, language: str | None = None
    ) -> ProductResponseSchema | ProductLanguageResponseSchema:
        ratings = [r.rating for r in product.ratings] if product.ratings else []
        average_rating = sum(ratings) / len(ratings) if ratings else None

        main_variant = None
        main_image = None
        current_price = 0  
        old_price = 0  
        
        color_codes = []
        sizes = []
        
        for variant in product.variants:
            if variant.color and variant.color.hex_code not in color_codes:
                color_codes.append(variant.color.hex_code)
            if variant.size and variant.size.size not in sizes:
                sizes.append(variant.size.size)
                
            if variant.is_main:
                main_variant = variant
                main_image = variant.images[0].image if variant.images else None
                current_price = variant.current_price
                old_price = variant.old_price
                break

        if not main_variant and product.variants:
            for variant in product.variants:
                if variant.images:
                    main_variant = variant
                    main_image = variant.images[0].image
                    current_price = variant.current_price
                    old_price = variant.old_price
                    break

        total_stock = sum(variant.amount for variant in product.variants)

        if language is None:
            return ProductLanguageResponseSchema(
                id=product.id,
                rating=average_rating,
                main_image=main_image,
                name=product.name, 
                description=product.description,
                product_information_id=product.product_information_id,
                warehouse_id=product.warehouse_id,
                subcategory_name=product.subcategory.name.get(language, ""),
                subcategory_id=product.subcategory_id,
                current_price=current_price,
                old_price=old_price,
                total_stock=total_stock,
                color_code=color_codes,
                size=sizes
            )
        
        return ProductResponseSchema(
            id=product.id,
            rating=average_rating,
            current_price=current_price,
            old_price=old_price,
            main_image=main_image,
            name=product.name.get(language, ""), 
            description=product.description.get(language) if product.description else None,
            product_information_id=product.product_information_id,
            warehouse_id=product.warehouse_id,
            subcategory_name=product.subcategory.name.get(language, ""),
            subcategory_id=product.subcategory_id,
            total_stock=total_stock,
            color_code=color_codes,
            size=sizes
        )


    async def get_products_by_category_id(
            self, limit: int, offset: int, category_id: int, language: str | None = None
    ) -> Sequence[ProductResponseSchema]:
        products_query = (
            select(Product)
            .join(Product.subcategory)
            .options(
                selectinload(Product.variants).selectinload(
                    ProductVariant.images),
                selectinload(Product.ratings),
            )
            .where(Subcategory.category_id == category_id)
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(products_query)
        products = result.scalars().all()
        return [self._build_product_response(product, language) for product in products]

    async def get_products_by_subcategory_id(
            self, limit, offset, subcategory_id, language: str | None = None
    ) -> Sequence[ProductResponseSchema | ProductLanguageResponseSchema]:
        products_query = (
            select(Product)
            .options(
                selectinload(Product.variants).selectinload(
                    ProductVariant.images),
                selectinload(Product.ratings),
            )
            .where(Product.subcategory_id == subcategory_id)
            .limit(limit)
            .offset(offset)
        )
        products = (await self.session.execute(products_query)).scalars().all()

        return [self._build_product_response(product, language) for product in products]

    async def create_product(self, data: ProductCreateSchema) -> ProductLanguageResponseSchema:
        new_product = Product(
            name=await translate_text(data.name),
            description=await translate_text(data.description) if data.description else {},
            product_information_id=data.product_information_id,
            warehouse_id=data.warehouse_id,
            subcategory_id=data.subcategory_id,
        )
        self.session.add(new_product)
        await self.session.commit()
        await self.session.refresh(new_product)
        
        await self.session.refresh(new_product, ['subcategory'])

        total_stock = 0 
        color_codes = [] 
        sizes = []

        return ProductLanguageResponseSchema(
            id=new_product.id,
            name=new_product.name,
            description=new_product.description,
            product_information_id=new_product.product_information_id,
            warehouse_id=new_product.warehouse_id,
            subcategory_id=new_product.subcategory_id,
            subcategory_name=new_product.subcategory.name.get("uz") if new_product.subcategory else "",
            total_stock=total_stock,
            color_code=color_codes,
            size=sizes,
            rating=None,
            current_price=0,
            old_price=0,
            main_image=None
        )

    async def update_product(
            self, product_id: int, data: ProductUpdateSchema
    ) -> MainProductResponseSchema | None:
        result = await self.session.execute(
            select(Product)
            .options(
                selectinload(Product.variants)
                .selectinload(ProductVariant.images)
            )
            .where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(product, field):
                setattr(product, field, value)

        self.session.add(product) 
        await self.session.commit()
        await self.session.refresh(product) 

        return await self.get_product_by_id(product_id)

    async def delete_product(self, product_id: int):
        query = (
            select(Product)
            .options(
                selectinload(Product.variants),
                selectinload(Product.ratings),
                selectinload(Product.wishlists) 
            )
            .where(Product.id == product_id)
        )
        result = await self.session.execute(query)
        product = result.scalars().first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        for variant in product.variants:
            await self.session.delete(variant)
        for rating in product.ratings:
            await self.session.delete(rating)
        for wish in product.wishlists:
            await self.session.delete(wish)

        await self.session.delete(product)
        await self.session.commit()

    async def get_product_stats(self, warehouse_id: int):
        order_stats = await self.__get_order_stats(warehouse_id)
        product_stats = await self.__get_product_finance_stats(warehouse_id)

        payment_stats = await self.__get_payment_stats(warehouse_id)

        # return ProductListResponse(
        #     all_orders=int(order_stats.total_orders or 0),
        #     completed_orders=int(order_stats.completed_orders or 0),
        #     canceled_orders=int(order_stats.canceled_orders or 0),
        #     in_process_orders=int(order_stats.in_process_orders or 0),
        #     total_product_variants=int(
        #         product_stats.total_product_variants or 0),
        #     total_sales=float(product_stats.total_sales or 0.0),
        #     total_come_in_price=float(
        #         product_stats.total_come_in_price or 0.0),
        #     total_current_price=float(
        #         product_stats.total_current_price or 0.0),
        #     total_profit=float((product_stats.total_sales or 0.0) -
        #                        (product_stats.total_come_in_price or 0.0)),
        #     card_orders_sum=float(payment_stats.card or 0.0),
        #     cash_orders_sum=float(payment_stats.cash or 0.0),
        #     debt_orders_sum=float(payment_stats.debt or 0.0),
        # )
        return {
            "order_stats": order_stats ,
            "product_stats": product_stats,
            "payment_stats": payment_stats,
        }

    async def __get_order_stats(self, warehouse_id: int):
        stmt = select(
            func.count(distinct(AdminOrder.id)).label("total_orders"),
            func.count(distinct(AdminOrder.id)).filter(
                AdminOrder.status == AdminOrderStatusEnum.completed
            ).label("completed_orders"),
            func.count(distinct(AdminOrder.id)).filter(
                AdminOrder.status == AdminOrderStatusEnum.cancelled
            ).label("canceled_orders"),
            func.count(distinct(AdminOrder.id)).filter(
                AdminOrder.status == AdminOrderStatusEnum.opened
            ).label("in_process_orders"),
        ).select_from(AdminOrder).join(
            AdminOrder.items
        ).join(
            AdminOrderItem.product_variant
        ).join(
            ProductVariant.product
        ).where(
            Product.warehouse_id == warehouse_id
        )

        result = await self.session.execute(stmt)
        row = result.first()
        return row._asdict() if row else {}

    async def __get_product_finance_stats(self, warehouse_id: int):
        stmt = select(
            func.count(ProductVariant.id).label("total_product_variants"),
            func.sum(
                AdminOrderItem.quantity * ProductVariant.current_price
            ).label("total_sales"),
            func.sum(
                AdminOrderItem.quantity * ProductVariant.come_in_price
            ).label("total_come_in_price"),
            func.sum(
                ProductVariant.current_price * ProductVariant.amount
            ).label("total_current_price"),
        ).select_from(AdminOrderItem).join(
            AdminOrderItem.product_variant
        ).join(
            ProductVariant.product
        ).join(
            AdminOrderItem.order
        ).where(
            and_(
                Product.warehouse_id == warehouse_id,
                AdminOrder.status == AdminOrderStatusEnum.completed
            )
        )

        result = await self.session.execute(stmt)
        row = result.first()
        return row._asdict() if row else {}

    async def __get_payment_stats(self, warehouse_id: int):
        stmt = select(
            func.sum(
                case(
                    (AdminOrder.payment_type ==
                     PaymentMethodEnum.card, AdminOrder.total_amount),
                    else_=0
                )
            ).label("card"),
            func.sum(
                case(
                    (AdminOrder.payment_type ==
                     PaymentMethodEnum.cash, AdminOrder.total_amount),
                    else_=0
                )
            ).label("cash"),
            func.sum(
                case(
                    (AdminOrder.payment_type ==
                     PaymentMethodEnum.debt, AdminOrder.total_amount),
                    else_=0
                )
            ).label("debt"),
        ).select_from(AdminOrder).join(
            AdminOrder.items
        ).join(
            AdminOrderItem.product_variant
        ).join(
            ProductVariant.product
        ).where(
            and_(
                Product.warehouse_id == warehouse_id,
                AdminOrder.status == AdminOrderStatusEnum.completed
            )
        )

        result = await self.session.execute(stmt)
        row = result.first()
        return row._asdict() if row else {}

    async def get_warehouse_stats(
            self,
            warehouse_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
    ):
        if not start_date and not end_date:
            return await self._get_monthly_stats(warehouse_id)
        else:
            return await self._get_custom_range_stats(
                warehouse_id, start_date, end_date
            )

    async def _get_monthly_stats(self, warehouse_id: int):
        monthly_stats = {}

        for month in range(1, 13):
            date_conditions = [extract("month", Product.created_at) == month]

            total_stats_query = self._build_total_stats_query(
                warehouse_id, date_conditions
            )
            on_sale_query = self._build_on_sale_query(
                warehouse_id, date_conditions)
            not_on_sale_query = self._build_not_on_sale_query(
                warehouse_id, date_conditions
            )

            try:
                total_result = await self.session.execute(total_stats_query)
                on_sale_result = await self.session.execute(on_sale_query)
                not_on_sale_result = await self.session.execute(not_on_sale_query)

                total_row = total_result.first()
                total_stats = tuple(total_row) if total_row else (
                    0, 0, 0, 0, 0, 0, 0)

                on_sale_row = on_sale_result.first()
                on_sale_stats = (
                    tuple(on_sale_row) if on_sale_row else (
                        0, 0, 0, 0, 0, 0, 0, 0)
                )

                not_on_sale_row = not_on_sale_result.first()
                not_on_sale_stats = (
                    tuple(not_on_sale_row) if not_on_sale_row else (
                        0, 0, 0, 0, 0)
                )

                monthly_stats[datetime(2025, month, 1).strftime("%B")] = {
                    "total_stats": {
                        "total_products": total_stats[0],
                        "total_variants": total_stats[1],
                        "total_come_in_price": total_stats[2],
                        "total_current_price": total_stats[3],
                        "total_amount": total_stats[4],
                        "low_stock_products": total_stats[5],
                        "out_of_stock_products": total_stats[6],
                    },
                    "on_sale_stats": {
                        "total_products": on_sale_stats[0],
                        "total_variants": on_sale_stats[1],
                        "total_come_in_price": on_sale_stats[2],
                        "total_current_price": on_sale_stats[3],
                        "total_amount": on_sale_stats[4],
                    },
                    "not_on_sale_stats": {
                        "total_products": not_on_sale_stats[0],
                        "total_variants": not_on_sale_stats[1],
                        "total_come_in_price": not_on_sale_stats[2],
                        "total_current_price": not_on_sale_stats[3],
                        "total_amount": not_on_sale_stats[4],
                    },
                }
            except Exception as e:
                print(
                    f"Error in get_warehouse_stats for month {month}: {str(e)}")
                raise

        return monthly_stats

    async def _get_custom_range_stats(
            self,
            warehouse_id: int,
            start_date: Optional[datetime],
            end_date: Optional[datetime],
    ):
        date_conditions = []
        if start_date:
            date_conditions.append(Product.created_at >= start_date)
        if end_date:
            date_conditions.append(Product.created_at <= end_date)

        total_stats_query = self._build_total_stats_query(
            warehouse_id, date_conditions)
        on_sale_query = self._build_on_sale_query(
            warehouse_id, date_conditions)
        not_on_sale_query = self._build_not_on_sale_query(
            warehouse_id, date_conditions)

        try:
            total_result = await self.session.execute(total_stats_query)
            on_sale_result = await self.session.execute(on_sale_query)
            not_on_sale_result = await self.session.execute(not_on_sale_query)

            total_row = total_result.first()
            total_stats = tuple(total_row) if total_row else (
                0, 0, 0, 0, 0, 0, 0)

            on_sale_row = on_sale_result.first()
            on_sale_stats = (
                tuple(on_sale_row) if on_sale_row else (0, 0, 0, 0, 0, 0, 0, 0)
            )

            not_on_sale_row = not_on_sale_result.first()
            not_on_sale_stats = (
                tuple(not_on_sale_row) if not_on_sale_row else (0, 0, 0, 0, 0)
            )

            return {
                "total_stats": {
                    "total_products": total_stats[0],
                    "total_variants": total_stats[1],
                    "total_come_in_price": total_stats[2],
                    "total_current_price": total_stats[3],
                    "total_amount": total_stats[4],
                    "low_stock_products": total_stats[5],
                    "out_of_stock_products": total_stats[6],
                },
                "on_sale_stats": {
                    "total_products": on_sale_stats[0],
                    "total_variants": on_sale_stats[1],
                    "total_come_in_price": on_sale_stats[2],
                    "total_current_price": on_sale_stats[3],
                    "total_amount": on_sale_stats[4],
                    "average_discount": on_sale_stats[5],
                    "min_discount": on_sale_stats[6],
                    "max_discount": on_sale_stats[7],
                },
                "not_on_sale_stats": {
                    "total_products": not_on_sale_stats[0],
                    "total_variants": not_on_sale_stats[1],
                    "total_come_in_price": not_on_sale_stats[2],
                    "total_current_price": not_on_sale_stats[3],
                    "total_amount": not_on_sale_stats[4],
                },
            }
        except Exception as e:
            print(f"Error in get_warehouse_stats: {str(e)}")
            raise

    def _build_total_stats_query(self, warehouse_id: int, date_conditions):
        query = (
            select(
                func.count(distinct(Product.id)).label("total_products"),
                func.count(ProductVariant.id).label("total_variants"),
                func.coalesce(
                    func.sum(ProductVariant.come_in_price *
                             ProductVariant.amount), 0
                ).label("total_come_in_price"),
                func.coalesce(
                    func.sum(ProductVariant.current_price *
                             ProductVariant.amount), 0
                ).label("total_current_price"),
                func.coalesce(func.sum(ProductVariant.amount),
                              0).label("total_amount"),
                func.count(case((ProductVariant.amount < 10, 1))).label(
                    "low_stock_products"
                ),
                func.count(case((ProductVariant.amount == 0, 1))).label(
                    "out_of_stock_products"
                ),
            )
            .select_from(Product)
            .outerjoin(ProductVariant)
            .where(Product.warehouse_id == warehouse_id)
        )

        if date_conditions:
            query = query.where(and_(*date_conditions))

        return query

    def _build_on_sale_query(self, warehouse_id: int, date_conditions):
        query = (
            select(
                func.count(distinct(Product.id)).label("total_products"),
                func.count(ProductVariant.id).label("total_variants"),
                func.coalesce(
                    func.sum(ProductVariant.come_in_price *
                             ProductVariant.amount), 0
                ).label("total_come_in_price"),
                func.coalesce(
                    func.sum(ProductVariant.current_price *
                             ProductVariant.amount), 0
                ).label("total_current_price"),
                func.coalesce(func.sum(ProductVariant.amount),
                              0).label("total_amount"),
                func.coalesce(func.avg(ProductVariant.discount), 0).label(
                    "average_discount"
                ),
                func.coalesce(func.min(ProductVariant.discount), 0).label(
                    "min_discount"
                ),
                func.coalesce(func.max(ProductVariant.discount), 0).label(
                    "max_discount"
                ),
            )
            .select_from(Product)
            .outerjoin(ProductVariant)
            .where(
                Product.warehouse_id == warehouse_id,
                ProductVariant.discount.isnot(None),
            )
        )

        if date_conditions:
            query = query.where(and_(*date_conditions))

        return query

    def _build_not_on_sale_query(self, warehouse_id: int, date_conditions):
        query = (
            select(
                func.count(distinct(Product.id)).label("total_products"),
                func.count(ProductVariant.id).label("total_variants"),
                func.coalesce(
                    func.sum(ProductVariant.come_in_price *
                             ProductVariant.amount), 0
                ).label("total_come_in_price"),
                func.coalesce(
                    func.sum(ProductVariant.current_price *
                             ProductVariant.amount), 0
                ).label("total_current_price"),
                func.coalesce(func.sum(ProductVariant.amount),
                              0).label("total_amount"),
            )
            .select_from(Product)
            .outerjoin(ProductVariant)
            .where(
                Product.warehouse_id == warehouse_id, ProductVariant.discount.is_(
                    None)
            )
        )

        if date_conditions:
            query = query.where(and_(*date_conditions))

        return query
