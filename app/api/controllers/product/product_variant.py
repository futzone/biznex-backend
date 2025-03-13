from typing import List, Optional
from fastapi import Depends, HTTPException, UploadFile

from app.api.repositories.product.product_variant import ProductVariantRepository
from app.api.schemas.product.product_variant import (
    ProductVariantCreateSchema,
    ProductVariantUpdateSchema,
    ProductVariantResponseSchema,
)


class ProductVariantController:
    def __init__(self, repo: ProductVariantRepository = Depends()):
        self.__repo = repo

    async def get_all_variants(self, warehouse_id) -> List[ProductVariantResponseSchema]:
        return await self.__repo.get_all_variants(warehouse_id)

    async def get_variants_for_product(
        self, product_id: int
    ) -> List[ProductVariantResponseSchema]:
        return await self.__repo.get_variants_for_product(product_id)

    async def get_variant(
        self, product_id: int, variant_id: int
    ) -> ProductVariantResponseSchema:
        data = await self.__repo.get_variant(product_id, variant_id)
        if not data:
            raise HTTPException(
                status_code=404, detail="Variant not found or product mismatch"
            )
        if data.is_main and data.product:
            data.product = data.product.model_copy(update={"main_product": True})
        return data

    async def get_product_by_barcode(
        self, barcode: int
    ) -> ProductVariantResponseSchema:
        data = await self.__repo.get_product_by_barcode(barcode)
        if not data:
            raise HTTPException(
                status_code=404, detail="Variant not found for given barcode"
            )
        return data

    async def create_variant(
        self,
        product_id: int,
        data: ProductVariantCreateSchema,
        pictures: Optional[List[str]] = None,
    ) -> ProductVariantResponseSchema:
        try:
            variant_resp = await self.__repo.create_variant(product_id, data, pictures)
            if variant_resp.is_main and variant_resp.product:
                variant_resp.product = variant_resp.product.model_copy(
                    update={"main_product": True}
                )
            return variant_resp
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def update_variant(
        self,
        product_id: int,
        variant_id: int,
        data: ProductVariantUpdateSchema,
        pictures: Optional[List[str]] = None,
    ) -> ProductVariantResponseSchema:
        variant_resp = await self.__repo.update_variant(
            product_id, variant_id, data, pictures
        )
        if variant_resp.is_main and variant_resp.product:
            variant_resp.product = variant_resp.product.model_copy(
                update={"main_product": True}
            )
        return variant_resp

    async def delete_variant(self, product_id: int, variant_id: int) -> None:
        await self.__repo.delete_variant(product_id, variant_id)
