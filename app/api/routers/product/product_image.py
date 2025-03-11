from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header, status
from starlette.requests import Request

from app.api.controllers.product.product_image import ProductImageController
from app.api.models.user import AdminUser
from app.api.schemas.product.product_image import (
    ProductImageCreateSchema,
    ProductImageUpdateSchema,
    ProductImageResponseSchema,
)
from app.api.utils.permission_checker import check_permission
from app.api.utils.user import AuthUtils
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.databases.postgres import get_general_session

router = APIRouter()


@router.get(
    "/", response_model=List[ProductImageResponseSchema], status_code=status.HTTP_200_OK
)
async def get_images(controller: ProductImageController = Depends()):
    return await controller.get_images()


@router.get(
    "/{image_id}/",
    response_model=ProductImageResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_image(image_id: int, controller: ProductImageController = Depends()):
    return await controller.get_image_by_id(image_id)


@router.post(
    "/", response_model=ProductImageResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_image(
    request: Request,
    data: ProductImageCreateSchema,
    controller: ProductImageController = Depends(),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
    session: AsyncSession = Depends(get_general_session),
):
    warehouse_id = int(request.headers.get('id'))
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="product_image",
        action="create",
    )

    return await controller.create_image(data)


@router.put(
    "/{image_id}/",
    response_model=ProductImageResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_image(
    request: Request,
    image_id: int,
    data: ProductImageUpdateSchema,
    controller: ProductImageController = Depends(),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
    session: AsyncSession = Depends(get_general_session),
):
    warehouse_id = int(request.headers.get('id'))
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="product_image",
        action="update",
    )

    return await controller.update_image(image_id, data)


@router.delete("/{image_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    request: Request,
    image_id: int,
    controller: ProductImageController = Depends(),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
    session: AsyncSession = Depends(get_general_session),
):
    warehouse_id = int(request.headers.get('id'))
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="product_image",
        action="delete",
    )
    await controller.delete_image(image_id)
