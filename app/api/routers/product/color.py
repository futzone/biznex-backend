# app/api/routers/product/color.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header, status
from starlette.requests import Request

from app.api.controllers.product.color import ColorController
from app.api.models.user import AdminUser
from app.api.schemas.product.color import (
    ColorCreateSchema,
    ColorLanguageResponseSchema,
    ColorUpdateSchema,
    ColorResponseSchema,
)
from app.api.utils.permission_checker import check_permission
from app.api.utils.user import AuthUtils
from app.core.databases.postgres import get_general_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/", response_model=List[ColorResponseSchema], status_code=status.HTTP_200_OK
)
async def get_colors(
        controller: ColorController = Depends(),
        language: str = Header(None, alias="language"),
):
    return await controller.get_colors(language=language)


@router.get(
    "/{color_id}/", response_model=ColorResponseSchema, status_code=status.HTTP_200_OK
)
async def get_color(
        color_id: int,
        controller: ColorController = Depends(),
    language: str = Header(None, alias="language"),
):
    return await controller.get_color_by_id(color_id, language=language)


@router.post(
    "/", response_model=ColorLanguageResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_color(
    request: Request,
    data: ColorCreateSchema,
    controller: ColorController = Depends(),
    session: AsyncSession = Depends(get_general_session),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),

):
    warehouse_id = int(request.headers.get('warehouse_id'))
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="color",
        action="create",
    )

    return await controller.create_color(data)


@router.put(
    "/{color_id}/", response_model=ColorUpdateSchema, status_code=status.HTTP_200_OK
)
async def update_color(
    request: Request,
    color_id: int,
    data: ColorUpdateSchema,
    controller: ColorController = Depends(),
    session: AsyncSession = Depends(get_general_session),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
):
    warehouse_id = int(request.headers.get('warehouse_id'))
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="color",
        action="create",
    )

    return await controller.update_color(color_id, data)


@router.delete("/{color_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_color(
    color_id: int,
    controller: ColorController = Depends(),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
    session: AsyncSession = Depends(get_general_session),
):
    if not current_admin.is_global_admin:
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail="You are teapot).",
        )


    await controller.delete_color(color_id)
