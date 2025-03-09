import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Date, and_, cast, distinct, func, select, text
from sqlalchemy.orm import joinedload, selectinload

from app.api.models.order import AdminOrder, AdminOrderItem
from app.api.models.product import Product, ProductVariant
from app.api.models.user import AdminUser, User
from app.api.models.warehouse import AdminWarehouse, Warehouse
from app.api.schemas.user import AdminDashboardResponse, BaseStats
from app.core.databases.postgres import get_general_session
from app.api.models.warehouse import admin_warehouse_roles
from app.core.models.enums import AdminOrderStatusEnum, OrderStatusEnum


class AdminRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def get_user_warehouse_role(
        self, user_id: int, warehouse_id: int
    ) -> Optional[AdminWarehouse]:
        query = (
            select(AdminWarehouse)
            .join(admin_warehouse_roles)
            .where(
                admin_warehouse_roles.c.admin_id == user_id,
                AdminWarehouse.warehouse_id == warehouse_id,
            )
        )
        result = await self.__session.execute(query)
        return result.scalar_one_or_none()

    async def get_warehouse_roles(self, warehouse_id: int) -> List[AdminWarehouse]:
        query = select(AdminWarehouse).where(
            AdminWarehouse.warehouse_id == warehouse_id
        )
        result = await self.__session.execute(query)
        return result.scalars().all()

    async def get_admin_warehouse_by_id(self, role_id: int) -> Optional[AdminWarehouse]:
        query = select(AdminWarehouse).where(AdminWarehouse.id == role_id)
        result = await self.__session.execute(query)
        return result.scalar_one_or_none()

    async def create_admin(self, admin: AdminUser, warehouse_role_id: int) -> AdminUser:
        try:
            self.__session.add(admin)
            await self.__session.flush()

            stmt = admin_warehouse_roles.insert().values(
                admin_id=admin.id, warehouse_role_id=warehouse_role_id
            )
            await self.__session.execute(stmt)

            await self.__session.commit()
            await self.__session.refresh(admin)

            return admin

        except IntegrityError:
            await self.__session.rollback()
            raise HTTPException(
                status_code=400, detail="Bu telefon raqamli admin allaqachon mavjud"
            )

    async def get_by_phone_number(self, phone_number: str) -> AdminUser:
        query = select(AdminUser).where(AdminUser.phone_number == phone_number)
        result = await self.__session.execute(query)
        return result.scalars().first()

    async def get_user_by_id(
        self, session: AsyncSession, user_id: int
    ) -> Optional[AdminUser]:
        result = await session.execute(
            select(AdminUser)
            .where(AdminUser.id == user_id)
            .options(
                selectinload(AdminUser.warehouse_roles).selectinload(
                    AdminWarehouse.warehouse
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_admin_warehouses(self, session: AsyncSession, user: AdminUser):
        result = await session.execute(
            select(AdminUser)
            .where(AdminUser.id == user.id)
            .options(
                selectinload(AdminUser.warehouse_roles).selectinload(
                    AdminWarehouse.warehouse
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_top_seller(
        self, 
        warehouse_id: int, 
        start_date: datetime = None, 
        end_date: datetime = None
    ):
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        end_date = end_date.replace(hour=23, minute=59, second=59)
        
        
        query = (
            select(
                AdminUser.id,
                AdminUser.full_name,
                AdminUser.phone_number,
                AdminUser.is_global_admin,
                AdminUser.profile_picture,
                AdminWarehouse.name.label("role_name"),
                func.count(distinct(AdminOrder.id)).label("order_count"),
                func.sum(AdminOrderItem.quantity).label("items_sold"),
                func.sum(AdminOrderItem.total_amount).label("total_revenue"),
                func.sum(AdminOrderItem.total_amount_with_discount).label("total_revenue_with_discount"),
                func.sum(
                    AdminOrderItem.total_amount_with_discount - 
                    (AdminOrderItem.quantity * ProductVariant.current_price)
                ).label("total_profit"),
                (func.sum(AdminOrderItem.total_amount_with_discount) / 
                func.count(distinct(AdminOrder.id))).label("average_order_value")
            )
            .join(AdminOrder, AdminOrder.by == AdminUser.id)
            .join(AdminOrderItem, AdminOrderItem.order_id == AdminOrder.id)
            .join(ProductVariant, ProductVariant.id == AdminOrderItem.product_variant_id)
            .join(admin_warehouse_roles, admin_warehouse_roles.c.admin_id == AdminUser.id)
            .join(AdminWarehouse, and_(
                AdminWarehouse.id == admin_warehouse_roles.c.warehouse_role_id,
                AdminWarehouse.warehouse_id == warehouse_id
            ))
            .where(
                and_(
                    AdminOrder.status == AdminOrderStatusEnum.completed,
                    AdminOrder.warehouse_id == warehouse_id,
                    # AdminOrder.created_at >= start_date,
                    # AdminOrder.created_at <= end_date
                )
            )
            .group_by(
                AdminUser.id,
                AdminUser.full_name,
                AdminUser.phone_number,
                AdminUser.is_global_admin,
                AdminUser.profile_picture,
                AdminWarehouse.name
            )
            .order_by(text("total_revenue_with_discount DESC"))
            .limit(10)
        )

        result = await self.__session.execute(query)
        return result.all()

    async def get_warehouse_by_id(self, warehouse_id: int):
        result = await self.__session.execute(
            select(Warehouse).where(Warehouse.id == warehouse_id)
        )
        return result.scalar_one_or_none()

    async def get_warehouse_by_owner_id(self, owner_id: int) -> Optional[Warehouse]:
        query = select(Warehouse).where(Warehouse.owner_id == owner_id)
        result = await self.__session.execute(query)
        return result.scalar_one_or_none()

    async def get_warehouse_role(
        self, warehouse_id: int, role_id: int
    ) -> Optional[AdminWarehouse]:
        query = select(AdminWarehouse).where(
            AdminWarehouse.warehouse_id == warehouse_id, AdminWarehouse.id == role_id
        )
        result = await self.__session.execute(query)
        return result.scalar_one_or_none()

    async def get_admins_by_warehouse_id(self, warehouse_id: int) -> List[AdminUser]:
        result = await self.__session.execute(
            select(AdminUser)
            .join(AdminUser.warehouse_roles)
            .where(AdminWarehouse.warehouse_id == warehouse_id)
            .options(joinedload(AdminUser.warehouse_roles))
        )
        return result.unique().scalars().all()

    async def get_admin_dashboard(self, warehouse_id: int) -> AdminDashboardResponse:
        today = datetime.utcnow()
        yesterday = today - timedelta(days=1)

        products_total = (await self.__session.execute(
            select(func.count(Product.id))
            .where(Product.warehouse_id == warehouse_id)
        )).scalar()

        products_today = (await self.__session.execute(
            select(func.count(ProductVariant.id))
            .join(Product, ProductVariant.product_id == Product.id)
            .where(and_(
                func.date(ProductVariant.created_at) == today,
                Product.warehouse_id == warehouse_id
            ))
        )).scalar()

        products_yesterday = (await self.__session.execute(
            select(func.count(ProductVariant.id))
            .join(Product, ProductVariant.product_id == Product.id)
            .where(and_(
                func.date(ProductVariant.created_at) == yesterday,
                Product.warehouse_id == warehouse_id
            ))
        )).scalar()

        orders_total = (await self.__session.execute(
            select(func.count(AdminOrder.id))
            .join(AdminOrder.items)
            .join(AdminOrderItem.product_variant)
            .join(ProductVariant.product)
            .where(AdminOrder.warehouse_id == warehouse_id)
        )).scalar()

        orders_today = (await self.__session.execute(
            select(func.count(AdminOrder.id))
            .join(AdminOrder.items)
            .join(AdminOrderItem.product_variant)
            .join(ProductVariant.product)
            .where(and_(
                func.date(AdminOrder.created_at) == today,
                AdminOrder.warehouse_id == warehouse_id
            ))
        )).scalar()

        orders_yesterday = (await self.__session.execute(
            select(func.count(AdminOrder.id))
            .join(AdminOrder.items)
            .join(AdminOrderItem.product_variant)
            .join(ProductVariant.product)
            .where(and_(
                func.date(AdminOrder.created_at) == yesterday,
                AdminOrder.warehouse_id == warehouse_id
            ))
        )).scalar()

        pending_total = (await self.__session.execute(
            select(func.count(AdminOrder.id))
            .join(AdminOrder.items)
            .join(AdminOrderItem.product_variant)
            .join(ProductVariant.product)
            .where(and_(
                AdminOrder.status == AdminOrderStatusEnum.opened,
                AdminOrder.warehouse_id == warehouse_id
            ))
        )).scalar()

        pending_today = (await self.__session.execute(
            select(func.count(AdminOrder.id))
            .join(AdminOrder.items)
            .join(AdminOrderItem.product_variant)
            .join(ProductVariant.product)
            .where(and_(
                AdminOrder.status == AdminOrderStatusEnum.opened,
                func.date(AdminOrder.created_at) == today,
                AdminOrder.warehouse_id == warehouse_id
            ))
        )).scalar()

        pending_yesterday = (await self.__session.execute(
            select(func.count(AdminOrder.id))
            .join(AdminOrder.items)
            .join(AdminOrderItem.product_variant)
            .join(ProductVariant.product)
            .where(and_(
                AdminOrder.status == AdminOrderStatusEnum.opened,
                func.date(AdminOrder.created_at) == yesterday,
                AdminOrder.warehouse_id == warehouse_id
            ))
        )).scalar()

        completed_total = (await self.__session.execute(
            select(func.count(AdminOrder.id))
            .join(AdminOrder.items)
            .join(AdminOrderItem.product_variant)
            .join(ProductVariant.product)
            .where(and_(
                AdminOrder.status == AdminOrderStatusEnum.completed,
                AdminOrder.warehouse_id == warehouse_id
            ))
        )).scalar()

        completed_today = (await self.__session.execute(
            select(func.count(AdminOrder.id))
            .join(AdminOrder.items)
            .join(AdminOrderItem.product_variant)
            .join(ProductVariant.product)
            .where(and_(
                AdminOrder.status == AdminOrderStatusEnum.completed,
                func.date(AdminOrder.created_at) == today,
                Product.warehouse_id == warehouse_id
            ))
        )).scalar()

        completed_yesterday = (await self.__session.execute(
            select(func.count(AdminOrder.id))
            .join(AdminOrder.items)
            .join(AdminOrderItem.product_variant)
            .join(ProductVariant.product)
            .where(and_(
                AdminOrder.status == AdminOrderStatusEnum.completed,
                func.date(AdminOrder.created_at) == yesterday,
                AdminOrder.warehouse_id == warehouse_id
            ))
        )).scalar()

        def calculate_growth(today_count: int, yesterday_count: int) -> float:
            if yesterday_count == 0:
                return 100.0 if today_count > 0 else 0.0
            return ((today_count - yesterday_count) / yesterday_count) * 100

        return AdminDashboardResponse(
            products=BaseStats(
                growth_rate=calculate_growth(products_today, products_yesterday),
                total_count=products_total
            ),
            orders=BaseStats(
                growth_rate=calculate_growth(orders_today, orders_yesterday),
                total_count=orders_total
            ),
            pending_orders=BaseStats(
                growth_rate=calculate_growth(pending_today, pending_yesterday),
                total_count=pending_total
            ),
            completed_orders=BaseStats(
                growth_rate=calculate_growth(completed_today, completed_yesterday),
                total_count=completed_total
            )
        )

    async def get_hourly_orders_today(self, warehouse_id: int):
        tashkent_tz = ZoneInfo('Asia/Tashkent')
        now_tashkent = datetime.now(timezone.utc).astimezone(tashkent_tz)
        
        start_of_day_tashkent = now_tashkent.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day_tashkent = now_tashkent.replace(hour=23, minute=59, second=59, microsecond=999999)

        start_of_day_utc = start_of_day_tashkent.astimezone(timezone.utc).replace(tzinfo=None)
        end_of_day_utc = end_of_day_tashkent.astimezone(timezone.utc).replace(tzinfo=None)

        query = (
            select(
                func.date_trunc(
                    text("'hour'"), 
                    func.timezone(text("'Asia/Tashkent'"), AdminOrder.updated_at)  
                ).label("hour"),
                func.count(AdminOrder.id).label("order_count")
            )
            .where(
                and_(
                    AdminOrder.status == AdminOrderStatusEnum.completed,
                    AdminOrder.updated_at >= start_of_day_utc,
                    AdminOrder.updated_at <= end_of_day_utc,
                    AdminOrder.warehouse_id == warehouse_id
                )
            )
            .group_by(
                func.date_trunc(
                    text("'hour'"), 
                    func.timezone(text("'Asia/Tashkent'"), AdminOrder.updated_at) 
                )
            ) 
        )

        result = await self.__session.execute(query)
        return result.all()