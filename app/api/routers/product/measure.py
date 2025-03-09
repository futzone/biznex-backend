# app/api/routers/product/measure.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status

from app.api.controllers.product.measure import MeasureController
from app.api.models.user import AdminUser
from app.api.schemas.product.measure import (
    MeasureCreateSchema,
    MeasureUpdateSchema,
    MeasureResponseSchema,
)
from app.api.utils.permission_checker import check_permission
from app.api.utils.user import AuthUtils
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.databases.postgres import get_general_session

router = APIRouter()


@router.get(
    "/", response_model=List[MeasureResponseSchema], status_code=status.HTTP_200_OK
)
async def get_measures(
    request: Request,
    controller: MeasureController = Depends(),
    session: AsyncSession = Depends(get_general_session),
):

    return await controller.get_measures()


@router.get(
    "/{measure_id}/",
    response_model=MeasureResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_measure(measure_id: int, controller: MeasureController = Depends()):
    return await controller.get_measure_by_id(measure_id)


@router.post(
    "/", response_model=MeasureResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_measure(
    data: MeasureCreateSchema,
    controller: MeasureController = Depends(),
    session: AsyncSession = Depends(get_general_session),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
):
    if not current_admin.is_global_admin:
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail="You are teapot).",
        )
    return await controller.create_measure(data)


@router.put(
    "/{measure_id}/",
    response_model=MeasureResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_measure(
    measure_id: int,
    data: MeasureUpdateSchema,
    controller: MeasureController = Depends(),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
):
    if not current_admin.is_global_admin:
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail="You are teapot).",
        )

    return await controller.update_measure(measure_id, data)


@router.delete("/{measure_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_measure(
    measure_id: int,
    controller: MeasureController = Depends(),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
):
    if not current_admin.is_global_admin:
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail="You are teapot).",
        )

    await controller.delete_measure(measure_id)
