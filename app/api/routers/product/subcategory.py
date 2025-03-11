from typing import List, Sequence, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Body, Header
from starlette.requests import Request

from app.api.controllers.product.subcategory import SubcategoryController
from app.api.models.user import AdminUser
from app.api.schemas.product.category import WarehouseCategoryResponse, WarehouseSubcategoryCreate
from app.api.schemas.product.subcategory import (
    SubcategoryCreateSchema,
    SubcategoryUpdateSchema,
    SubcategoryResponseSchema,
    SubcategoryCreateResponseSchema,
)
from app.api.utils.permission_checker import check_permission
from app.api.utils.user import AuthUtils
from app.core.databases.postgres import get_general_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/",
    response_model=Sequence[SubcategoryResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_subcategories(
        request: Request,
        category_id: Optional[int] = None,
        controller: SubcategoryController = Depends(),
        language: str = Header(default="uz", alias="language"),
) -> Sequence[SubcategoryResponseSchema]:
    warehouse_id = int(request.headers.get('warehouse_id'))
    return await controller.get_subcategories(category_id, language, warehouse_id)


@router.get(
    "/{subcategory_id}/",
    response_model=SubcategoryResponseSchema | SubcategoryCreateResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_subcategory(
        subcategory_id: int,
        controller: SubcategoryController = Depends(),
        language: str = Header(None, alias="language"),
) -> SubcategoryResponseSchema | SubcategoryCreateResponseSchema:
    subcategory = await controller.get_subcategory_by_id(subcategory_id, language)
    if not subcategory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subcategory not found",
        )
    return subcategory


@router.post(
    "/",
    response_model=SubcategoryCreateResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_subcategory(
        data: SubcategoryCreateSchema,
        controller: SubcategoryController = Depends(),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),

) -> SubcategoryCreateResponseSchema:
    return await controller.create_subcategory(data)


@router.post(
    "warehouse_subcategory/",
    response_model=WarehouseCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subcategory(
        data: WarehouseSubcategoryCreate,
        controller: SubcategoryController = Depends(),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),

) -> WarehouseCategoryResponse:
    return await controller.create_warehouse_subcategory(data)


@router.put(
    "/{subcategory_id}/",
    response_model=SubcategoryCreateResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_subcategory(
        request: Request,
        subcategory_id: int,
        data: SubcategoryUpdateSchema,
        controller: SubcategoryController = Depends(),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
        session: AsyncSession = Depends(get_general_session),
) -> SubcategoryCreateResponseSchema:
    warehouse_id = int(request.headers.get('warehouse_id'))
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="subcategory",
        action="update",
    )

    return await controller.update_subcategory(subcategory_id, data)


@router.delete("/{subcategory_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subcategory(
        request: Request,
        subcategory_id: int,
        controller: SubcategoryController = Depends(),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
        session: AsyncSession = Depends(get_general_session),
) -> None:
    warehouse_id = int(request.headers.get('warehouse_id'))
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="subcategory",
        action="delete",
    )

    await controller.delete_subcategory(subcategory_id)
