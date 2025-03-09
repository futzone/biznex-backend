from datetime import datetime, timedelta, timezone
import json
import secrets
from typing import List, Optional
from zoneinfo import ZoneInfo
import bcrypt
from fastapi import Depends, HTTPException, Request, Response, status

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.models.user import AdminUser
from app.api.models.warehouse import AdminWarehouse
from app.api.repositories.admin import AdminRepository
from app.api.schemas.user import (
    AdminDashboardResponse,
    AdminUserCreate,
    AdminUserResponse,
    AdminUserResponsee,
    AdminWarehouseResponse,
    TopSellerResponse,
)
from app.api.schemas.user import WarehousePermissionResponse
from app.api.utils.user import AuthUtils
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import settings
from app.core.databases.postgres import get_general_session

settings = settings.get_settings()


class AdminController:
    def __init__(
        self,
        admin_repo: AdminRepository = Depends(),
        session: Session = Depends(get_general_session),
    ):
        self.__admin_repo = admin_repo
        self.__session = session

    async def get_user_owner_role(
        self, user_id: int, warehouse_id: int
    ) -> Optional[AdminWarehouse]:
        return await self.__admin_repo.get_user_warehouse_role(
            int(user_id), warehouse_id
        )

    async def get_warehouse_roles(self, warehouse_id: int) -> List[AdminWarehouse]:
        return await self.__admin_repo.get_warehouse_roles(int(warehouse_id))

    async def create_user(
        self, admin_create: AdminUserCreate, current_user: AdminUser
    ) -> AdminUserResponse:
        generated_password = secrets.token_urlsafe(10)
        hashed_password = bcrypt.hashpw(
            generated_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        warehouse_role = await self.__admin_repo.get_admin_warehouse_by_id(
            admin_create.warehouse_role_id
        )
        if (
            not warehouse_role
            or warehouse_role.warehouse_id != admin_create.warehouse_id
        ):
            raise HTTPException(status_code=404, detail="Warehouse role topilmadi")

        new_admin = AdminUser(
            full_name=admin_create.full_name,
            phone_number=admin_create.phone_number,
            password=hashed_password,
            is_global_admin=False,
            profile_picture=admin_create.profile_picture,
        )

        created_admin = await self.__admin_repo.create_admin(
            admin=new_admin, warehouse_role_id=warehouse_role.id
        )

        return AdminUserResponse(
            id=created_admin.id,
            full_name=created_admin.full_name,
            phone_number=created_admin.phone_number,
            is_global_admin=created_admin.is_global_admin,
            password=generated_password,
        )

    async def login_admin(self, phone_number: str, password: str, response: Response):
        if not phone_number or not password:
            raise HTTPException(
                status_code=400, detail="Phone number and password are required."
            )

        admin = await self.__admin_repo.get_by_phone_number(phone_number)

        if not admin or not bcrypt.checkpw(
            password.encode("utf-8"), admin.password.encode("utf-8")
        ):
            raise HTTPException(
                status_code=401, detail="Incorrect phone number or password."
            )

        # Token yaratish
        access_token = await AuthUtils.create_access_token(
            data={"sub": str(admin.id), "role": str("admin")},
            expired_minute=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

        refresh_token = await AuthUtils.create_refresh_token(
            data={"sub": str(admin.id), "role": str("admin")},
            expired_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 * 360,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "admin": {
                "id": admin.id,
                "full_name": admin.full_name,
                "phone_number": admin.phone_number,
                "is_global_admin": admin.is_global_admin,
            },
        }

    async def get_is_global_admin(self, user_id: int, db_session: AsyncSession) -> bool:
        query = select(AdminUser.is_global_admin).where(AdminUser.id == user_id)
        result = await db_session.execute(query)
        is_global_admin = result.scalar() 
        return is_global_admin
    
    async def get_top_seller(
        self, 
        warehouse_id: int, 
        start_date: datetime = None, 
        end_date: datetime = None
    ) -> List[TopSellerResponse]:
        top_sellers = await self.__admin_repo.get_top_seller(
            warehouse_id=warehouse_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return [
            TopSellerResponse(
                id=seller.id,
                full_name=seller.full_name,
                phone_number=seller.phone_number,
                is_global_admin=seller.is_global_admin,
                profile_picture=seller.profile_picture,
                role_name=seller.role_name,
                order_count=seller.order_count,
                items_sold=seller.items_sold,
                total_revenue=seller.total_revenue,
                total_revenue_with_discount=seller.total_revenue_with_discount,
                total_profit=seller.total_profit,
                average_order_value=seller.average_order_value
            )
            for seller in top_sellers
        ]

    async def get_current_admin_user(
        self, request: Request, session: AsyncSession
    ) -> AdminUserResponse:
        token = await AuthUtils.get_current_user_from_cookie(request)
        if not token:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user = await self.__admin_repo.get_user_by_id(session, int(token["sub"]))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        formatted_warehouses = [
            {
                "id": wh.warehouse.id,
                "name": wh.warehouse.name,
                "address": wh.warehouse.address,
                "description": wh.warehouse.description,
                "latitude": wh.warehouse.latitude,
                "longitude": wh.warehouse.longitude,
                "owner_id": wh.warehouse.owner_id,
                "owner_phone_number": wh.warehouse.owner_phone_number,
            }
            for wh in user.warehouse_roles
        ]

        return AdminUserResponse(
            id=user.id,
            full_name=user.full_name,
            phone_number=user.phone_number,
            profile_picture=user.profile_picture,
            is_global_admin=user.is_global_admin,
            password=user.password,
            warehouses=formatted_warehouses,
        )

    async def get_warehouse_admins(self, warehouse_id: int) -> List[AdminUserResponse]:
        try:
            admins = await self.__admin_repo.get_warehouse_admins(warehouse_id)

            for admin in admins:
                for warehouse_role in admin.warehouse_roles:
                    if isinstance(warehouse_role.permissions, str):
                        warehouse_role.permissions = json.loads(
                            warehouse_role.permissions
                        )
                    elif isinstance(warehouse_role.permissions, dict):
                        warehouse_role.permissions = {
                            k: v if isinstance(v, list) else [v]
                            for k, v in warehouse_role.permissions.items()
                        }

            return admins
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {str(e)}",
            )

    async def get_admins_by_warehouse_id(
        self, warehouse_id: int
    ) -> List[AdminUserResponsee]:
        admin_users = await self.__admin_repo.get_admins_by_warehouse_id(warehouse_id)

        if not admin_users:
            raise HTTPException(
                status_code=404, detail="No admins found for this warehouse"
            )

        return [
            AdminUserResponsee(
                id=admin.id,
                full_name=admin.full_name,
                phone_number=admin.phone_number,
                is_global_admin=admin.is_global_admin,
                profile_picture=admin.profile_picture,
                password=None,
                role_name=(
                    admin.warehouse_roles[0].name if admin.warehouse_roles else None
                ),
            )
            for admin in admin_users
        ]

    async def get_admin_dashboard(
            self,
            warehouse_id, 
    ) -> AdminDashboardResponse:

        return await self.__admin_repo.get_admin_dashboard(warehouse_id)
        
    async def get_hourly_orders_today_formatted(self, warehouse_id: int):
        hourly_orders = await self.__admin_repo.get_hourly_orders_today(warehouse_id)

        tashkent_tz = ZoneInfo('Asia/Tashkent')
        now_tashkent = datetime.now(timezone.utc).astimezone(tashkent_tz)
        
        start_of_day_tashkent = now_tashkent.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day_tashkent = now_tashkent
        
        result = {}
        current_time = start_of_day_tashkent
        while current_time <= end_of_day_tashkent:
            display_hour_key = current_time.strftime("%H:00")
            result[display_hour_key] = 0
            current_time += timedelta(hours=1)
        
        for order in hourly_orders:
            order_hour_tashkent = order.hour.astimezone(tashkent_tz)
            display_hour_key = order_hour_tashkent.strftime("%H:00")
            result[display_hour_key] = order.order_count
        
        return result