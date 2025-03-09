from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.api.repositories.product.banner import BannerRepository
from app.api.repositories.product.promotion import PromotionRepository
from app.api.schemas.product.promotion import PromotionCreate, PromotionResponse, PromotionUpdate

class PromotionController:
    def __init__(
            self, 
            promotion_repository: PromotionRepository = Depends()
        ):
            self.promotion_repository = promotion_repository

    async def get_promotions(self, warehouse_id: int) -> List[PromotionResponse]:
        return await self.promotion_repository.get_promotions(warehouse_id)
    
    async def create_promotion(self, data: PromotionCreate, warehouse_id: int) -> PromotionResponse:
        return await self.promotion_repository.create_promotion(data, warehouse_id)