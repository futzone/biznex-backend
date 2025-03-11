from datetime import datetime, timedelta
from dateutil import parser
from typing import List, Optional

from dateutil.parser import isoparse
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request, Response, status
from sqlalchemy import select, func

from app.api.controllers.admin import AdminController
from app.api.controllers.product.product import ProductController
from app.api.models.product import Product
from app.api.models.user import AdminUser
from app.api.repositories.product.product import ProductRepository
from app.api.schemas.product.product import WarehouseStatsResponse
from app.api.utils.permission_checker import check_permission
from app.api.utils.user import AuthUtils
from app.core.databases.postgres import get_general_session
from app.api.schemas.user import AdminDashboardResponse, AdminUserCreate, AdminUserResponse, AdminUserResponsee, BaseStats, TopSellerFilterRequest, TopSellerResponse

from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/create", response_model=AdminUserResponse)
async def create_admin(
        admin_create: AdminUserCreate,
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
        session: AsyncSession = Depends(get_general_session),
        controller: AdminController = Depends(),
):
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=admin_create.warehouse_id,
        model_name="product_image",
        action="create",
    )
    return await controller.create_user(admin_create, current_admin)


@router.post("/login")
async def login_admin(
        phone_number: str,
        password: str,
        response: Response,
        controller: AdminController = Depends(),
):
    return await controller.login_admin(phone_number, password, response)


@router.get(
    "/adminme", response_model=AdminUserResponse, status_code=status.HTTP_200_OK
)
async def get_current_admin_user(
        request: Request,
        controller: AdminController = Depends(),
        session: AsyncSession = Depends(get_general_session),
):
    return await controller.get_current_admin_user(request=request, session=session)


@router.get("/get_admins/{warehouse_id}", response_model=List[AdminUserResponsee])
async def get_admins_by_warehouse(
        warehouse_id: int,
        controller: AdminController = Depends(),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
        session: AsyncSession = Depends(get_general_session),
):
    """
    Berilgan warehouse_id bo'yicha adminlarni qaytarish.
    """

    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="admin",
        action="read",
    )

    return await controller.get_admins_by_warehouse_id(warehouse_id)


@router.get(
    "/get_top_seller",
    response_model=List[TopSellerResponse],
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/get_top_seller",
    response_model=List[TopSellerResponse],
    status_code=status.HTTP_200_OK,
)
async def get_top_sellers(
        request: Request,
        start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
        current_admin: AdminUser = Depends(get_current_admin_user),
        controller: AdminController = Depends(),
        session: AsyncSession = Depends(get_general_session)
):
    warehouse_id = int(request.headers.get('id'))
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="admin",
        action="read",
    )

    parsed_start_date = None
    parsed_end_date = None

    if start_date:
        try:
            parsed_start_date = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )

    if end_date:
        try:
            parsed_end_date = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )

    if parsed_start_date is None:
        parsed_start_date = datetime.now() - timedelta(days=30)

    if parsed_end_date is None:
        parsed_end_date = datetime.now()

    return await controller.get_top_seller(
        warehouse_id=warehouse_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date
    )


@router.get("/warehouses/{warehouse_id}/stats_order_product")
async def get_products_by_sale_status(
        warehouse_id: int,
        session: AsyncSession = Depends(get_general_session),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
):
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="admin",
        action="read",
    )

    repo = ProductRepository(session)
    controller = ProductController(repo)
    return await controller.get_products_by_sale_status(warehouse_id)


@router.get("/warehouses/{warehouse_id}/stats", response_model=WarehouseStatsResponse)
async def get_warehouse_stats(
        warehouse_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        session: AsyncSession = Depends(get_general_session),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
):
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="admin",
        action="read",
    )

    if start_date:
        try:
            start_date = isoparse(start_date)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            end_date = isoparse(end_date)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid end_date format")

    repo = ProductRepository(session)
    controller = ProductController(repo)
    stats = await controller.get_warehouse_stats(warehouse_id, start_date, end_date)

    return {
        "warehouse_id": warehouse_id,
        "stats": stats,
    }


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
        request: Request,
        session: AsyncSession = Depends(get_general_session),
        controller: AdminController = Depends(),
        # current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
):
    # await check_permission(
    #     session=session,
    #     admin_id=current_admin.id,
    #     warehouse_id=warehouse_id,
    #     model_name="admin",
    #     action="read",
    # )
    # now = datetime.now()
    # result = await session.execute(
    #     select(func.count(Product.id)).where(
    #         Product.warehouse_id == warehouse_id,
    #         Product.created_at >= now,
    #     )
    # )
    # total_products = result.scalar()
    warehouse_id = int(request.headers.get('id'))

    print(warehouse_id)

    return await controller.get_admin_dashboard(warehouse_id)


@router.get("/dashboard/stats")
async def get_dashboard_stats(
        request: Request,
        controller: AdminController = Depends(),
        # current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
):
    # await check_permission(
    #     session=session,
    #     admin_id=current_admin.id,
    #     warehouse_id=warehouse_id,
    #     model_name="admin",
    #     action="read",
    # )

    warehouse_id = int(request.headers.get('id'))
    return await controller.get_hourly_orders_today_formatted(warehouse_id)
