from http.client import HTTPException
from typing import List
from fastapi import APIRouter, Depends, Header, status
from starlette.requests import Request

from app.api.controllers.product.size import SizeController
from app.api.models.user import AdminUser
from app.api.schemas.product.size import (
    SizeCreateSchema,
    SizeUpdateSchema,
    SizeResponseSchema,
    SizeCreateResponseSchema,
)
from app.api.utils.permission_checker import check_permission
from app.api.utils.user import AuthUtils
from app.core.databases.postgres import get_general_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/wh/{warehouse_id}",
    response_model=List[SizeResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_sizes(
        warehouse_id: int | None = None,
        controller: SizeController = Depends(),
        language: str = Header(default="uz", alias="language"),
):
    return await controller.get_sizes(warehouse_id, language)


@router.get(
    "/{size_id}/",
    response_model=SizeResponseSchema | SizeCreateResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_size(
        size_id: int,
        controller: SizeController = Depends(),
        language: str = Header(default="uz", alias="language"),
) -> SizeResponseSchema | SizeCreateResponseSchema:
    return await controller.get_size_by_id(size_id, language)


@router.post(
    "/", response_model=SizeCreateResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_size(
        request: Request,
        data: SizeCreateSchema,
        controller: SizeController = Depends(),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
        session: AsyncSession = Depends(get_general_session),
):
    try:
        print(request.headers)
        warehouse_id = int(request.headers.get('warehouse_id'))

        await check_permission(
            session=session,
            admin_id=current_admin.id,
            warehouse_id=warehouse_id,
            model_name="size",
            action="create",
        )

        return await controller.create_size(data)
    except Exception as e:
        print("\n\n\n\n HEADERS: ")
        print(request.headers)
        print("\n\n\n\n")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{request.headers}",
        )


@router.put(
    "/{size_id}/",
    response_model=SizeCreateResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_size(
        request: Request,
        size_id: int,
        data: SizeUpdateSchema,
        controller: SizeController = Depends(),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
        session: AsyncSession = Depends(get_general_session),
):
    warehouse_id = int(request.headers.get('warehouse_id'))
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="size",
        action="update",
    )

    return await controller.update_size(size_id, data)


@router.delete("/{size_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_size(
        request: Request,
        size_id: int,
        controller: SizeController = Depends(),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
        session: AsyncSession = Depends(get_general_session),
):
    warehouse_id = int(request.headers.get('warehouse_id'))
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="size",
        action="delete",
    )

    await controller.delete_size(size_id)
