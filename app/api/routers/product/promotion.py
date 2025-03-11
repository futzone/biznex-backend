from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from starlette.requests import Request

from app.api.controllers.product.promotion import PromotionController
from app.api.models.user import AdminUser
from app.api.routers.admin import get_current_admin_user
from app.api.schemas.product.promotion import *
from app.core.databases.postgres import get_general_session

router = APIRouter()


@router.get("/", response_model=List[PromotionResponse])
async def get_promotions(
        request: Request,
        controller: PromotionController = Depends(),
        # current_admin: AdminUser = Depends(get_current_admin_user),
        session: AsyncSession = Depends(get_general_session),
):
    warehouse_id = request.headers.get('warehouse_id')
    return await controller.get_promotions(warehouse_id)

@router.post("/", response_model=PromotionResponse)
async def create_promotion(
        request: Request,
        data: PromotionCreate,
        controller: PromotionController = Depends(),
        # current_admin: AdminUser = Depends(get_current_admin_user),
        session: AsyncSession = Depends(get_general_session),
):
    warehouse_id = request.headers.get('warehouse_id')
    return await controller.create_promotion(data, warehouse_id)