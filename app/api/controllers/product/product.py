from datetime import datetime
from typing import List, Optional, Sequence, Union
from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.api.constants.languages import languages
from app.api.repositories.product.product import ProductRepository
from app.api.repositories.product.product_information import (
    ProductInformationRepository,
)
from app.api.repositories.product.subcategory import SubcategoryRepository
from app.api.repositories.warehouse import WarehouseRepository
from app.api.schemas.product.product import (
    ProductFilterSchema,
    ProductResponseSchema,
    ProductCreateSchema,
    MainProductResponseSchema,
    ProductUpdateSchema,
    ProductVariantSalesResponse,
    WarehouseStatsResponse,
    ProductListResponse,
    ProductResponse,
    ProductLanguageResponseSchema,
    MainProductLanguageResponseSchema,
)
from app.api.utils.check_language import check_language


class ProductController:
    def __init__(
        self,
        repository: ProductRepository = Depends(),
        warehouse_repository: WarehouseRepository = Depends(),
        subcategory_repository: SubcategoryRepository = Depends(),
        product_information_repository: ProductInformationRepository = Depends(),
    ):
        self.repository = repository
        self.warehouse_repository = warehouse_repository
        self.subcategory_repository = subcategory_repository
        self.product_information_repository = product_information_repository

    async def get_products(
        self, limit, offset, warehouse_id, language: str | None
    ) -> Sequence[ProductResponseSchema | ProductLanguageResponseSchema]:
        await check_language(language)
        if warehouse_id:
            return await self.repository.get_products_by_warehouse_id(
                limit, offset, warehouse_id, language
            )
        return await self.repository.get_products(limit, offset, language)

    async def get_all_products(
        self, warehouse_id: int, language: str | None
    ):
        await check_language(language)
        return await self.repository.get_all_products(warehouse_id, language)

    async def get_little_products_left(
        self, warehouse_id: int, limit: int, offset: int, language: str | None, amount: int
    ) -> Sequence[ProductResponseSchema | ProductLanguageResponseSchema]:
        await check_language(language)
        return await self.repository.get_little_products_left(
            warehouse_id, limit, offset, language, amount=amount
        )
    
    async def get_product_variant_sales(
        self, 
        language: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        warehouse_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProductVariantSalesResponse]:
        result = await self.repository.get_product_variant_sales(
            language=language,
            start_date=start_date,
            end_date=end_date,
            warehouse_id=warehouse_id,
            limit=limit,
            offset=offset
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="No sales data found for the specified criteria."
            )
            
        return result
    async def get_product_by_id(
        self, product_id: int, language: str | None
    ) -> MainProductResponseSchema | MainProductLanguageResponseSchema:
        await check_language(language)
        product = await self.repository.get_product_by_id(product_id, language)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )
        return product

    async def search_products(
        self,
        filters: ProductFilterSchema,
        language: str,
        limit,
        offset
    ) -> ProductListResponse:
        if filters.min_price and filters.max_price and filters.min_price > filters.max_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid price range"
            )

        products, total = await self.repository.search_products(filters, language, limit, offset)
        return ProductListResponse(
            products=products,
            total=total,
            limit=limit,
            offset=offset
        )

    async def get_products_by_category_id(
        self, limit, offset, category_id, language: str | None
    ) -> Sequence[ProductResponseSchema]:
        await check_language(language)
        products = await self.repository.get_products_by_category_id(
            limit, offset, category_id, language
        )
        if not products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Products not found in this category",
            )
        return products

    async def get_products_by_subcategory_id(
        self, limit, offset, subcategory_id, language
    ) -> Sequence[ProductResponseSchema]:
        await check_language(language)
        products = await self.repository.get_products_by_subcategory_id(
            limit, offset, subcategory_id, language
        )
        if not products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Products not found in this subcategory",
            )

        return products

    async def get_recomended_products(self, subcategory_id, limit, offset, language) -> List[ProductResponseSchema]:
        await check_language(language)
        return await self.repository.get_recomended_products(limit=limit, offset=offset, language=language, subcategory_id=subcategory_id)

    async def _is_valid_data_to_post(self, data: ProductCreateSchema) -> None:
        warehouse = await self.warehouse_repository.get_warehouse_by_id(
            data.warehouse_id
        )
        if warehouse is None:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        subcategory = await self.subcategory_repository.get_subcategory_by_id(
            data.subcategory_id, languages[0]
        )
        if subcategory is None:
            raise HTTPException(
                status_code=404, detail="Subcategory not found")
        product_information = await self.product_information_repository.get_info_by_id(
            data.product_information_id
        )
        if product_information is None:
            raise HTTPException(
                status_code=404, detail="Product information not found")

    async def create_product(
        self, data: ProductCreateSchema
    ) -> ProductLanguageResponseSchema:
        await self._is_valid_data_to_post(data)
        return await self.repository.create_product(data)

    async def _is_valid_data_update(self, data: ProductUpdateSchema) -> None:
        if data.warehouse_id:
            warehouse = await self.warehouse_repository.get_warehouse_by_id(
                data.warehouse_id
            )
            if warehouse is None:
                raise HTTPException(
                    status_code=404, detail="Warehouse not found")
        if data.subcategory_id:
            subcategory = await self.subcategory_repository.get_subcategory_by_id(
                data.subcategory_id, languages[0]
            )
            if subcategory is None:
                raise HTTPException(
                    status_code=404, detail="Subcategory not found")
        if data.product_information_id:
            product_information = (
                await self.product_information_repository.get_info_by_id(
                    data.product_information_id
                )
            )
            if product_information is None:
                raise HTTPException(
                    status_code=404, detail="Product information not found"
                )

        if data.name:
            data.name = {
                "uz": data.name,
                "ru": data.name,
                "en": data.name,
            }

        if data.description:
            data.description = {
                "uz": data.description,
                "ru": data.description,
                "en": data.description,
            }

    async def update_product(
        self, product_id: int, data: ProductUpdateSchema
    ) -> ProductResponseSchema:
        await self._is_valid_data_update(data)
        return await self.repository.update_product(product_id, data)

    async def delete_product(self, product_id: int) -> None:
        await self.repository.delete_product(product_id)

    async def get_products_by_sale_status(self, warehouse_id: int):
        stats = await self.repository.get_product_stats(warehouse_id)

        if not stats:
            raise HTTPException(status_code=404, detail="No products found")

        return stats

    async def get_warehouse_stats(
        self, warehouse_id: int, start_date: datetime, end_date: datetime
    ):
        stats = await self.repository.get_warehouse_stats(
            warehouse_id, start_date, end_date
        )

        return stats
