from typing import List, Sequence
from fastapi import (
    APIRouter,
    Depends,
    Header,
    status,
)
from starlette.requests import Request

from app.api.constants.languages import languages
from app.api.controllers.product.product_information import ProductInformationController
from app.api.models.user import AdminUser
from app.api.schemas.product.product_information import (
    ProductInformationCreateSchema,
    ProductInformationUpdateSchema,
    ProductInformationResponseSchema,
    ProductInformationLanguageResponseSchema,
)

from sqlalchemy.ext.asyncio import AsyncSession
from app.api.utils.permission_checker import check_permission
from app.api.utils.user import AuthUtils
from app.core.databases.postgres import get_general_session

router = APIRouter()


@router.get(
    "/wh/{warehouse_id}/",
    response_model=Sequence[
        ProductInformationResponseSchema | ProductInformationLanguageResponseSchema
    ],
    status_code=status.HTTP_200_OK,
)
async def get_all_product_info(
    warehouse_id: int | None = None,
    controller: ProductInformationController = Depends(),
    language: str = Header(None, alias="language"),
) -> Sequence[
    ProductInformationResponseSchema | ProductInformationLanguageResponseSchema
]:
    return await controller.get_all_info(warehouse_id, language)


@router.get(
    "/{info_id}/",
    response_model=ProductInformationResponseSchema
    | ProductInformationLanguageResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_product_info(
    info_id: int,
    controller: ProductInformationController = Depends(),
    language: str = Header(None, alias="language"),
) -> ProductInformationResponseSchema | ProductInformationLanguageResponseSchema:
    return await controller.get_info_by_id(info_id, language)


@router.post(
    "/",
    response_model=ProductInformationLanguageResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_product_info(
    request: Request,
    data: ProductInformationCreateSchema,
    controller: ProductInformationController = Depends(),
    current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
    session: AsyncSession = Depends(get_general_session),
) -> ProductInformationLanguageResponseSchema:
    warehouse_id = request.headers.get('warehouse_id')
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="product_information",
        action="create",
    )

    return await controller.create_info(data)


@router.put(
    "/{info_id}/",
    response_model=ProductInformationLanguageResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_product_info(
    info_id: int,
    data: ProductInformationUpdateSchema,
    controller: ProductInformationController = Depends(),
) -> ProductInformationLanguageResponseSchema:
    return await controller.update_info(info_id, data)


@router.delete("/{info_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_info(
    info_id: int, controller: ProductInformationController = Depends()
) -> None:
    await controller.delete_info(info_id)
