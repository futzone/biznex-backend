from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo

from app.api.models.product import ProductVariant, Promotion
from app.api.schemas.product.promotion import PromotionCreate, PromotionUpdate, PromotionResponse
from app.core.databases.postgres import get_general_session


# repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from fastapi import Depends
from typing import List, Optional
from datetime import datetime

class PromotionRepository:
    def __init__(
            self, 
            session: AsyncSession = Depends(get_general_session)
        ):
        self.session = session

    async def get_promotions(self, warehouse_id: int) -> List[PromotionResponse]:
        stmt = select(Promotion).where(Promotion.warehouse_id == warehouse_id)
        result = await self.session.execute(stmt)
        promotions = result.scalars().all()
        
        return [PromotionResponse.model_validate(promo) for promo in promotions]
    
    async def create_promotion(self, data: PromotionCreate, warehouse_id: int) -> PromotionResponse:
        promo_data = data.dict(exclude={"warehouse_id", "product_variant_ids"})

        promotion = Promotion(
            **promo_data,
            warehouse_id=warehouse_id,
        )

        self.session.add(promotion)

        if data.product_variant_ids:
            product_variants = await self.session.execute(
                select(ProductVariant).where(ProductVariant.id.in_(data.product_variant_ids))
            )
            promotion.product_variants = product_variants.scalars().all()

        await self.session.commit()
        await self.session.refresh(promotion)

        return PromotionResponse.model_validate(promotion)