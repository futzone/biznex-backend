import random
from typing import List, Optional, Union, Sequence
from fastapi import Depends, HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
import os
import uuid

from app.core.databases.postgres import get_general_session
from app.api.models.product import ProductVariant, ProductImage, Size
from app.api.schemas.product.product_variant import (
    ProductVariantCreateSchema,
    ProductVariantUpdateSchema,
    ProductVariantResponseSchema,
)


class ProductVariantRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def _build_variant_response(
            self, variant: ProductVariant
    ) -> ProductVariantResponseSchema:
        product = variant.product
        # if product and isinstance(product.name, dict):
        #     product_name = product.name.get("en", "")
        #     # Optionally, you can assign back a converted value:
        #     product.name = product_name
        #
        # # Convert size description similarly.
        # if variant.size and isinstance(variant.size.description, dict):
        #     size_desc = variant.size.description.get("en", "")
        #     variant.size.description = size_desc

        main_img = None
        for img in variant.images:
            if img.is_main:
                main_img = img.image
                break

        resp = ProductVariantResponseSchema.model_validate(variant)
        resp.main_image = main_img
        return resp

    async def _build_response(
        self, variants: Union[ProductVariant, Sequence[ProductVariant]]
    ) -> Union[ProductVariantResponseSchema, List[ProductVariantResponseSchema]]:
        if isinstance(variants, list):
            responses = []
            for variant in variants:
                responses.append(await self._build_variant_response(variant))
            return responses
        else:
            return await self._build_variant_response(variants)

    async def get_all_variants(self, warehouse_id) -> List[ProductVariantResponseSchema]:
        result = await self.__session.execute(
            select(ProductVariant)
            .join(ProductVariant.product)
            .where(ProductVariant.product.has(warehouse_id=warehouse_id))
            .options(
                selectinload(ProductVariant.product),
                selectinload(ProductVariant.color),
                selectinload(ProductVariant.size),
                selectinload(ProductVariant.measure),
                selectinload(ProductVariant.images),
            )
        )
        variants = result.scalars().all()
        return await self._build_response(variants)

    async def get_variants_for_product(
        self, product_id: int
    ) -> List[ProductVariantResponseSchema]:
        result = await self.__session.execute(
            select(ProductVariant)
            .where(ProductVariant.product_id == product_id)
            .options(
                selectinload(ProductVariant.product),
                selectinload(ProductVariant.color),
                selectinload(ProductVariant.size),
                selectinload(ProductVariant.measure),
                selectinload(ProductVariant.images),
            )
        )
        variants = result.scalars().all()
        return await self._build_response(variants)

    async def get_product_by_barcode(
            self, barcode: int
    ) -> Optional[ProductVariantResponseSchema]:
        result = await self.__session.execute(
            select(ProductVariant)
            .where(ProductVariant.barcode == barcode)
            .options(
                joinedload(ProductVariant.product),
                joinedload(ProductVariant.color),
                joinedload(ProductVariant.size),
                joinedload(ProductVariant.measure),
                joinedload(ProductVariant.images),
            )
        )
        variant_obj = result.unique().scalar_one_or_none()
        if not variant_obj:
            return None
        return await self._build_response(variant_obj)

    async def get_variant(
            self, product_id: int, variant_id: int
    ) -> Optional[ProductVariantResponseSchema]:
        result = await self.__session.execute(
            select(ProductVariant)
            .where(
                ProductVariant.id == variant_id, ProductVariant.product_id == product_id
            )
            .options(
                joinedload(ProductVariant.product),
                joinedload(ProductVariant.color),
                joinedload(ProductVariant.size),
                joinedload(ProductVariant.measure),
                joinedload(ProductVariant.images),
            )
        )
        variant_obj = result.unique().scalar_one_or_none()
        if not variant_obj:
            return None
        return await self._build_response(variant_obj)

    async def  create_variant(
            self,
            product_id: int,
            data: ProductVariantCreateSchema,
            pictures: Optional[List[str]] = None,
    ) -> ProductVariantResponseSchema:
        
        if data.barcode == 0:
            data.barcode = await self._generate_unique_barcode()
        
        barcode_query = select(ProductVariant).where(ProductVariant.barcode == data.barcode)
        existing_variant = await self.__session.execute(barcode_query)
        existing_variant = existing_variant.scalar_one_or_none()

        if existing_variant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Barcode {data.barcode} is already in use.",
            )

        if data.size_id is not None:
            query = select(Size).where(Size.id == data.size_id)
            result = await self.__session.execute(query)
            size_obj = result.scalar_one_or_none()
            if size_obj is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid size_id provided: {data.size_id}"
                )
        variant_obj = ProductVariant(product_id=product_id, **data.model_dump())
        self.__session.add(variant_obj)
        await self.__session.commit()
        await self.__session.refresh(variant_obj)

        if pictures:
            await self._add_pictures(variant_obj, pictures)

        return await self._reload_and_build(variant_obj.id)

    async def update_variant(
            self,
            product_id: int,
            variant_id: int,
            data: ProductVariantUpdateSchema,
            pictures: Optional[List[UploadFile]] = None,
    ) -> ProductVariantResponseSchema:
        result = await self.__session.execute(
            select(ProductVariant)
            .where(
                ProductVariant.id == variant_id, ProductVariant.product_id == product_id
            )
            .options(joinedload(ProductVariant.images))
        )
        variant_obj = result.unique().scalar_one_or_none()
        if not variant_obj:
            raise HTTPException(
                status_code=404, detail="ProductVariant not found or product mismatch"
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(variant_obj, field, value)

        self.__session.add(variant_obj)
        await self.__session.commit()
        await self.__session.refresh(variant_obj)


        if pictures:
            await self._add_pictures(variant_obj, pictures)

        return await self._reload_and_build(variant_obj.id)

    async def delete_variant(self, product_id: int, variant_id: int) -> None:
        result = await self.__session.execute(
            select(ProductVariant).where(
                ProductVariant.id == variant_id, ProductVariant.product_id == product_id
            )
        )
        variant_obj = result.scalar_one_or_none()
        if not variant_obj:
            raise HTTPException(
                status_code=404, detail="Variant not found or product mismatch"
            )

        await self.__session.delete(variant_obj)
        await self.__session.commit()

    async def _generate_unique_barcode(self) -> int:
        while True:
            new_barcode = random.randint(100000000000, 999999999999)
            
            barcode_query = select(ProductVariant).where(ProductVariant.barcode == new_barcode)
            existing_variant = await self.__session.execute(barcode_query)
            existing_variant = existing_variant.scalar_one_or_none()

            if not existing_variant:
                return new_barcode

    async def _reload_and_build(self, variant_id: int) -> ProductVariantResponseSchema:
        result = await self.__session.execute(
            select(ProductVariant)
            .where(ProductVariant.id == variant_id)
            .options(
                joinedload(ProductVariant.product),
                joinedload(ProductVariant.color),
                joinedload(ProductVariant.size),
                joinedload(ProductVariant.measure),
                joinedload(ProductVariant.images),
            )
        )
        reloaded = result.unique().scalar_one_or_none()
        if not reloaded:
            raise HTTPException(
                status_code=404, detail="Variant not found after reload"
            )
        return await self._build_response(reloaded)

    async def _add_pictures(self, variant_obj: ProductVariant, pictures: List[str]):
        for filename in pictures:
            pic_obj = ProductImage(
                product_variant_id=variant_obj.id,
                image=filename,
                alt_text=filename,
                is_main=False,
            )
            self.__session.add(pic_obj)

        await self.__session.commit()
        await self.__session.refresh(variant_obj)
