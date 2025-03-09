from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

from app.api.models.product import Banner, ProductVariant
from app.api.schemas.product.banner import BannerCreate, BannerUpdate
from app.core.databases.postgres import get_general_session


# repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from fastapi import Depends
from typing import List, Optional
from datetime import datetime

class BannerRepository:
    def __init__(
            self, 
            db: AsyncSession = Depends(get_general_session)
        ):
        self.db = db

    async def create(self, banner_data: BannerCreate) -> Banner:
        try:
            start_date = banner_data.start_date if banner_data.start_date.tzinfo is None else banner_data.start_date.astimezone().replace(tzinfo=None)
            end_date = banner_data.end_date if banner_data.end_date.tzinfo is None else banner_data.end_date.astimezone().replace(tzinfo=None)

            stmt = select(ProductVariant).where(
                ProductVariant.id.in_(banner_data.product_variant_ids)
            )
            result = await self.db.execute(stmt)
            product_variants = result.scalars().all()

            banner_dict = banner_data.model_dump(exclude={'product_variant_ids'})
            banner_dict['start_date'] = start_date
            banner_dict['end_date'] = end_date
            
            banner = Banner(**banner_dict)
            banner.product_variants = product_variants

            self.db.add(banner)
            await self.db.flush()

            for variant in product_variants:
                if not variant.old_price:
                    variant.old_price = variant.current_price
                variant.discount = banner.discount_percentage
                variant.current_price = variant.old_price * (1 - banner.discount_percentage / 100)

            await self.db.commit()
            await self.db.refresh(banner)

            return banner

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create banner: {str(e)}"
            )


    async def get_by_id(self, banner_id: int) -> Optional[Banner]:
        stmt = select(Banner).where(Banner.id == banner_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Banner]:
        stmt = select(Banner).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_active_banners(self) -> List[Banner]:
        stmt = select(Banner).where(
            Banner.is_active == True,
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update(self, banner_id: int, banner_data: BannerUpdate) -> Optional[Banner]:
        banner = await self.get_by_id(banner_id)
        if not banner:
            return None

        update_data = banner_data.model_dump(exclude_unset=True)
        
        if 'product_variant_ids' in update_data:
            product_variant_ids = update_data.pop('product_variant_ids')
            stmt = select(ProductVariant).where(
                ProductVariant.id.in_(product_variant_ids)
            )
            result = await self.db.execute(stmt)
            new_variants = result.scalars().all()

            for variant in banner.product_variants:
                if variant.old_price:
                    variant.current_price = variant.old_price
                    variant.discount = None
                    variant.old_price = None

            banner.product_variants = new_variants
            for variant in new_variants:
                if not variant.old_price:
                    variant.old_price = variant.current_price
                variant.discount = banner.discount_percentage
                variant.current_price = variant.old_price * (1 - banner.discount_percentage / 100)

        for key, value in update_data.items():
            setattr(banner, key, value)

        await self.db.commit()
        await self.db.refresh(banner)
        return banner

    async def delete(self, banner_id: int) -> bool:
        banner = await self.get_by_id(banner_id)
        if not banner:
            return False

        for variant in banner.product_variants:
            if variant.old_price:
                variant.current_price = variant.old_price
                variant.discount = None
                variant.old_price = None

        await self.db.delete(banner)
        await self.db.commit()
        return True
