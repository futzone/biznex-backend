from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api.controllers.product.banner import BannerController
from app.api.models.user import AdminUser
from app.api.routers.admin import get_current_admin_user
from app.api.schemas.product.banner import BannerCreate, BannerResponse, BannerUpdate
from app.core.databases.postgres import get_general_session

router = APIRouter()


@router.get("/active", response_model=List[BannerResponse])
async def get_active_banners(
    controller: BannerController = Depends(),
):
    
    return await controller.get_active_banners()


@router.post("/", response_model=BannerResponse)
async def create_banner(
    banner_data: BannerCreate,
    session: AsyncSession = Depends(get_general_session),
    current_user: AdminUser = Depends(get_current_admin_user),
    controller: BannerController = Depends(),
):
    
    
    return await controller.create_banner(banner_data)

@router.get("/{banner_id}", response_model=BannerResponse)
async def get_banner(
    banner_id: int,
    controller: BannerController = Depends(),
):
    
    return await controller.get_banner(banner_id)

@router.get("/", response_model=List[BannerResponse])
async def get_banners(
    skip: int = 0,
    limit: int = 100,
    current_user: AdminUser = Depends(get_current_admin_user),
    controller: BannerController = Depends(),
):
    
    return await controller.get_banners(skip, limit)



@router.put("/{banner_id}", response_model=BannerResponse)
async def update_banner(
    banner_id: int,
    banner_data: BannerUpdate,
    current_user: AdminUser = Depends(get_current_admin_user),
    controller: BannerController = Depends(),
):
    

    return await controller.update_banner(banner_id, banner_data)

@router.delete("/{banner_id}")
async def delete_banner(
    banner_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    controller: BannerController = Depends(),
):
    
    return await controller.delete_banner(banner_id)