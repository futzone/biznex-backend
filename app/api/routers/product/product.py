from datetime import datetime
from typing import Sequence, List, Optional, Any, Coroutine
from fastapi import (
    APIRouter,
    Depends,
    Header,
    Query,
    status,
    HTTPException,
    Form,
    File,
    UploadFile,
)
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

# Import your controllers
from app.api.controllers.product.product import ProductController
from app.api.controllers.product.product_variant import ProductVariantController

# Import your Pydantic schemas for Product
from app.api.models.user import AdminUser
from app.api.routers.admin import get_current_admin_user
from app.api.schemas.product.product import (
    ProductCreateSchema,
    MainProductResponseSchema,
    ProductFilterSchema,
    ProductListResponse,
    ProductUpdateSchema,
    ProductResponseSchema,
    ProductLanguageResponseSchema,
    MainProductLanguageResponseSchema,
    ProductVariantSalesResponse,
)

from app.api.schemas.product.product_variant import (
    ProductVariantCreateSchema,
    ProductVariantUpdateSchema,
    ProductVariantResponseSchema,
)
from app.api.utils.permission_checker import check_permission
from app.api.utils.user import AuthUtils
from app.core.databases.postgres import get_general_session

router = APIRouter()


@router.get(
    "/",
    response_model=Sequence[ProductResponseSchema |
                            ProductLanguageResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_products(
        limit: int = Query(10, alias="limit", ge=1),
        offset: int = Query(0, alias="offset", ge=0),
        controller: ProductController = Depends(),
        warehouse_id: Optional[int] = Header(None, alias="warehouse_id"),
        language: str = Header(None, alias="language"),
) -> Sequence[ProductResponseSchema | ProductLanguageResponseSchema]:
    return await controller.get_products(limit=limit, offset=offset, language=language, warehouse_id=warehouse_id)


@router.get(
    "/offline",
    status_code=status.HTTP_200_OK,
)
async def get_all_products(
        request: Request,
        controller: ProductController = Depends(),
        language: str = Header(None, alias="language"),
):
    warehouse_id = int(request.headers.get('id'))
    return await controller.get_all_products(warehouse_id=warehouse_id, language=language)


@router.get(
    "/little_products_left",
    response_model=Sequence[ProductResponseSchema | ProductLanguageResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_little_products_left(
        request: Request,
        limit: int = Query(10, alias="limit", ge=1),
        offset: int = Query(0, alias="offset", ge=0),
        amount: int = Query(10, alias="amount", ge=1),
        controller: ProductController = Depends(),
        language: str = Header(None, alias="language"),
) -> Sequence[ProductResponseSchema | ProductLanguageResponseSchema]:
    warehouse_id = int(request.headers.get('id'))
    return await controller.get_little_products_left(limit=limit, offset=offset, warehouse_id=warehouse_id, language=language, amount=amount)


@router.get(
    "/product_variant_sales",
    response_model=List[ProductVariantSalesResponse],
    status_code=status.HTTP_200_OK,
)
async def get_product_variant_sales(
        start_date: Optional[datetime] = Query(None, description="Filter sales from this date"),
        end_date: Optional[datetime] = Query(None, description="Filter sales until this date"),
        warehouse_id: Optional[int] = Query(None, description="Filter by warehouse ID"),
        session: AsyncSession = Depends(get_general_session),
        current_user: AdminUser = Depends(get_current_admin_user),
        controller: ProductController = Depends(),
        limit: int = Query(50, alias="limit", ge=1),
        offset: int = Query(0, alias="offset", ge=0),
        language: str = Header(..., alias="language"),

):
    return await controller.get_product_variant_sales(
        language=language,
        start_date=start_date,
        end_date=end_date,
        warehouse_id=warehouse_id,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{product_id}/",
    response_model=MainProductResponseSchema | MainProductLanguageResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_product(
        product_id: int,
        controller: ProductController = Depends(),
        language: str = Header(None, alias="language"),
) -> MainProductResponseSchema | MainProductLanguageResponseSchema:
    return await controller.get_product_by_id(product_id, language)


@router.get(
    "/ct/{category_id}/",
    response_model=Sequence[ProductResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_products_by_category(
        category_id: int,
        limit: int = Query(10, alias="limit", ge=1),
        offset: int = Query(0, alias="offset", get=0),
        controller: ProductController = Depends(),
        language: str = Header(None, alias="language"),
) -> Sequence[ProductResponseSchema]:
    return await controller.get_products_by_category_id(
        category_id=category_id, limit=limit, offset=offset, language=language
    )


@router.get(
    "/sb/{subcategory_id}/",
    response_model=Sequence[ProductResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_products_by_subcategory_id(
        subcategory_id: int,
        limit: int = Query(10, alias="limit", ge=1),
        offset: int = Query(0, alias="offset", get=0),
        controller: ProductController = Depends(),
        language: str = Header(None, alias="language"),
) -> Sequence[ProductResponseSchema]:
    return await controller.get_products_by_subcategory_id(
        limit, offset, subcategory_id, language
    )


@router.get(
    "/product/search/",
    response_model=ProductListResponse,
    status_code=status.HTTP_200_OK,
)
async def filter_products(
        language: str = Header('uz', alias="language"),
        query: Optional[str] = Query(None, min_length=2),
        category_id: Optional[int] = Query(None),
        subcategory_id: Optional[int] = Query(None),
        color_id: Optional[list] = Query(None),
        size_id: Optional[list] = Query(None),
        measure_id: Optional[int] = Query(None),
        min_price: Optional[float] = Query(None, ge=0),
        max_price: Optional[float] = Query(None, ge=0),
        has_discount: Optional[bool] = Query(None),
        min_discount: Optional[float] = Query(None, ge=0, le=100),
        max_discount: Optional[float] = Query(None, ge=0, le=100),
        in_stock: Optional[bool] = Query(None),
        sort_by: str = Query('created_at', regex='^(created_at|price|discount)$'),
        sort_order: str = Query('desc', regex='^(asc|desc)$'),
        limit: int = Query(10, ge=1, le=100),
        offset: int = Query(0, ge=0),
        controller: ProductController = Depends()
):
    filters = ProductFilterSchema(
        query=query,
        category_id=category_id,
        subcategory_id=subcategory_id,
        color_id=color_id,
        size_id=size_id,
        measure_id=measure_id,
        min_price=min_price,
        max_price=max_price,
        has_discount=has_discount,
        min_discount=min_discount,
        max_discount=max_discount,
        in_stock=in_stock,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return await controller.search_products(
        filters=filters,
        language=language,
        limit=limit,
        offset=offset
    )


@router.get(
    "/recomended/{subcategory_id}",
    response_model=List[ProductResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_recomended_products(
        subcategory_id: int,
        limit: int = Query(10, alias="limit", ge=1),
        offset: int = Query(0, alias="offset", get=0),
        language: str = Header(..., alias="language"),
        controller: ProductController = Depends(),

):
    return await controller.get_recomended_products(subcategory_id, limit, offset, language)


@router.post(
    "/",
    response_model=ProductLanguageResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
        data: ProductCreateSchema,
        controller: ProductController = Depends(),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
        session: AsyncSession = Depends(get_general_session),
) -> ProductLanguageResponseSchema:
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=data.warehouse_id,
        model_name="product",
        action="create",
    )

    return await controller.create_product(data)


@router.put(
    "/{product_id}/",
    response_model=ProductResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_product(
        product_id: int,
        data: ProductUpdateSchema,
        controller: ProductController = Depends(),
        session: AsyncSession = Depends(get_general_session),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
) -> ProductResponseSchema:
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=data.warehouse_id,
        model_name="product",
        action="update",
    )

    return await controller.update_product(product_id, data)


@router.delete("/{product_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
        request: Request,
        product_id: int,
        controller: ProductController = Depends(),
        session: AsyncSession = Depends(get_general_session),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
) -> None:
    """
    Delete product by ID
    """

    warehouse_id = int(request.headers.get('id'))

    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="product",
        action="delete",
    )

    await controller.delete_product(product_id)


# ------------------------------------------------------------------
# PRODUCT VARIANT ROUTES (Nested)
# e.g.: /products/{product_id}/variants
# ------------------------------------------------------------------

@router.get(
    "/offline/variants/",
    response_model=List[ProductVariantResponseSchema],
    status_code=status.HTTP_200_OK,
    tags=["Product variants"],
)
async def get_all_variants(
        request: Request,
        controller: ProductVariantController = Depends(),
):
    warehouse_id = int(request.headers.get('id'))
    return await controller.get_all_variants(warehouse_id)


@router.get(
    "/{product_id}/variants/",
    response_model=List[ProductVariantResponseSchema],
    status_code=status.HTTP_200_OK,
    tags=["Product variants"],
)
async def get_variants_for_product(
        product_id: int, controller: ProductVariantController = Depends(),
):
    return await controller.get_variants_for_product(product_id)


@router.get(
    "/{product_id}/variants/{variant_id}/",
    response_model=ProductVariantResponseSchema,
    status_code=status.HTTP_200_OK,
    tags=["Product variants"],
)
async def get_single_variant(
        product_id: int, variant_id: int, controller: ProductVariantController = Depends()
):
    return await controller.get_variant(product_id, variant_id)


@router.get(
    "/product/{barcode}/",
    response_model=ProductVariantResponseSchema,
    status_code=status.HTTP_200_OK,
    tags=["Product variants"],
)
async def get_product_by_barcode(
        barcode: int, controller: ProductVariantController = Depends()
):
    return await controller.get_product_by_barcode(barcode)


@router.post(
    "/{product_id}/variants/",
    response_model=ProductVariantResponseSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Product variants"],
)
async def create_variant(
        request: Request,
        product_id: int,
        barcode: Optional[int] = Form(None),
        come_in_price: float = Form(...),
        current_price: float = Form(...),
        old_price: Optional[float] = Form(None),
        discount: Optional[float] = Form(None),
        is_main: bool = Form(False),
        amount: float = Form(...),
        weight: Optional[float] = Form(None),
        color_id: Optional[int] = Form(None),
        size_id: Optional[int] = Form(None),
        measure_id: int = Form(...),
        pictures: List[str] = File(None),
        controller: ProductVariantController = Depends(),
        session: AsyncSession = Depends(get_general_session),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
) -> ProductVariantResponseSchema:
    warehouse_id = int(request.headers.get('id'))
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="product_variant",
        action="create",
    )
    new_barcode = barcode if barcode is not None else 0

    try:
        data = ProductVariantCreateSchema(
            barcode=new_barcode,
            come_in_price=come_in_price,
            current_price=current_price,
            old_price=old_price,
            discount=discount,
            is_main=is_main,
            amount=amount,
            color_id=color_id,
            size_id=size_id,
            measure_id=measure_id,
            weight=weight,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return await controller.create_variant(product_id, data, pictures)


@router.put(
    "/{product_id}/variants/{variant_id}/",
    response_model=ProductVariantResponseSchema,
    status_code=status.HTTP_200_OK,
    tags=["Product variants"],
)
async def update_variant(
        request: Request,
        product_id: int,
        variant_id: int,
        barcode: Optional[int] = Form(None),
        come_in_price: Optional[float] = Form(None),
        current_price: Optional[float] = Form(None),
        old_price: Optional[float] = Form(None),
        discount: Optional[float] = Form(None),
        is_main: Optional[bool] = Form(None),
        amount: Optional[float] = Form(None),
        weight: Optional[float] = Form(None),
        color_id: Optional[int] = Form(None),
        size_id: Optional[int] = Form(None),
        measure_id: Optional[int] = Form(None),
        pictures: List[str] = Form(None),
        controller: ProductVariantController = Depends(),
        session: AsyncSession = Depends(get_general_session),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
) -> ProductVariantResponseSchema:
    warehouse_id = int(request.headers.get('id'))
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="product_variant",
        action="update",
    )

    try:
        data = ProductVariantUpdateSchema(
            barcode=barcode,
            come_in_price=come_in_price,
            current_price=current_price,
            old_price=old_price,
            discount=discount,
            is_main=is_main,
            amount=amount,
            color_id=color_id,
            size_id=size_id,
            measure_id=measure_id,
            weight=weight,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return await controller.update_variant(product_id, variant_id, data, pictures)


@router.delete(
    "/{product_id}/variants/{variant_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Product variants"],
)
async def delete_variant(
        request: Request,
        product_id: int,
        variant_id: int,
        controller: ProductVariantController = Depends(),
        session: AsyncSession = Depends(get_general_session),
        current_admin: AdminUser = Depends(AuthUtils.get_current_admin_user),
):
    warehouse_id = int(request.headers.get('id'))
    await check_permission(
        session=session,
        admin_id=current_admin.id,
        warehouse_id=warehouse_id,
        model_name="product_variant",
        action="delete",
    )

    await controller.delete_variant(product_id, variant_id)
