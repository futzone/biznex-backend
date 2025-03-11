import os
import uuid
from typing import List, Sequence, Optional
from fastapi import (
    APIRouter,
    Depends,
    Header,
    status,
    File,
    Form,
    UploadFile,
    HTTPException,
)
from pydantic import ValidationError
from starlette.requests import Request

from app.api.controllers.product.category import CategoryController
from app.api.controllers.warehouse import WarehouseController
from app.api.models.user import AdminUser
from app.api.schemas.product.category import (
    CategoryCreateSchema,
    CategoryUpdateSchema,
    CategoryResponseSchema,
    CategoryCreateResponseSchema,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.user import AdminUserResponse
from app.api.utils.permission_checker import check_permission
from app.api.utils.user import AuthUtils
from app.core.databases.postgres import get_general_session
from app.api.controllers.admin import AdminController

router = APIRouter()

controller = AdminController()


@router.get(
    "/", status_code=status.HTTP_200_OK, response_model=List[CategoryResponseSchema]
)
async def get_warehouse_categories(
        language: str = Header(None, alias="language"),
        warehouse_id: int = Header(None, alias="warehouse_id"),
        controller: CategoryController = Depends(),
):
    if warehouse_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found",
        )
    return await controller.get_warehouse_categories(warehouse_id, language)


@router.get(
    "/{category_id}/",
    response_model=CategoryResponseSchema | CategoryCreateResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_category(
        category_id: int,
        warehouse_id: int = Header(None, alias="warehouse_id"),
        language: str = Header("uz", alias="language"),
        controller: CategoryController = Depends(),
) -> CategoryResponseSchema | CategoryCreateResponseSchema:
    category = await controller.get_warehouse_category_by_id(warehouse_id, category_id, language)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category


@router.post(
    "/",
    response_model=CategoryCreateResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
        request: Request,
        data: CategoryCreateSchema,
        controller: CategoryController = Depends(),
        warehouse_controller: WarehouseController = Depends(),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
        session: AsyncSession = Depends(get_general_session),
) -> CategoryCreateResponseSchema:
    warehouse_id = request.headers.get('warehouse_id')
    warehouse = await warehouse_controller.get_warehouse_by_id(warehouse_id)

    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="category",
        action="create",
    )

    try:
        data = CategoryCreateSchema(
            name=data.name, description=data.description, image=data.image
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )

    return await controller.create_category(warehouse.id, data)


@router.put(
    "/{category_id}/",
    response_model=CategoryCreateResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_category(
        request: Request,
        category_id: int,
        data: Optional[CategoryUpdateSchema] = None,
        controller: CategoryController = Depends(),
        language: str = Header("uz", alias="language"),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
        session: AsyncSession = Depends(get_general_session),
) -> CategoryCreateResponseSchema:
    warehouse_id = request.headers.get('warehouse_id')
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="category",
        action="update",
    )

    old_category = await controller.get_category_by_id(warehouse_id, category_id, language)
    if not old_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found for update",
        )
    old_image_path = old_category.image
    new_image_path = old_image_path
    if data.image is not None:
        if old_image_path and os.path.isfile(old_image_path):
            try:
                os.remove(old_image_path)
            except OSError as e:
                pass
        new_image_path = data.image
    try:
        update_data = data.model_dump(exclude_unset=True)
        update_data["image"] = new_image_path if "image" in update_data else old_image_path
        data = CategoryUpdateSchema(**update_data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )

    return await controller.update_category(category_id, data)


@router.delete("/{category_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
        request: Request,
        category_id: int,
        controller: CategoryController = Depends(),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
        session: AsyncSession = Depends(get_general_session),
) -> None:
    warehouse_id = request.headers.get('warehouse_id')
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="category",
        action="delete",
    )

    old_category = await controller.get_warehouse_category_by_id(warehouse_id, category_id, language="uz")
    if not old_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found for delete",
        )
    if old_category.image and os.path.isfile(old_category.image):
        try:
            os.remove(old_category.image)
        except OSError:
            pass

    await controller.delete_category(category_id)
    return
