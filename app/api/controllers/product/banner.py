from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.api.repositories.product.banner import BannerRepository
from app.api.schemas.product.banner import BannerCreate, BannerResponse, BannerUpdate

class BannerController:
    def __init__(
            self, 
            banner_repository: BannerRepository = Depends()
        ):
            self.banner_repository = banner_repository

    async def create_banner(self, banner_data: BannerCreate) -> BannerResponse:
        try:
            banner = await self.banner_repository.create(banner_data)
            return BannerResponse.model_validate(banner)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def get_banner(self, banner_id: int) -> BannerResponse:
        banner = await self.banner_repository.get_by_id(banner_id)
        if not banner:
            raise HTTPException(status_code=404, detail="Banner not found")
        return BannerResponse.model_validate(banner)

    async def get_banners(self, skip: int = 0, limit: int = 100) -> List[BannerResponse]:
        banners = await self.banner_repository.get_all(skip, limit)
        return [BannerResponse.model_validate(banner) for banner in banners]

    async def get_active_banners(self) -> List[BannerResponse]:
        banners = await self.banner_repository.get_active_banners()

        if banners is None:
            raise HTTPException(status_code=404, detail="Banner not found")

        return [BannerResponse.model_validate(banner) for banner in banners]

    async def update_banner(self, banner_id: int, banner_data: BannerUpdate) -> BannerResponse:
        banner = await self.banner_repository.update(banner_id, banner_data)
        if not banner:
            raise HTTPException(status_code=404, detail="Banner not found")
        return BannerResponse.model_validate(banner)

    async def delete_banner(self, banner_id: int) -> dict:
        if not await self.banner_repository.delete(banner_id):
            raise HTTPException(status_code=404, detail="Banner not found")
        return {"message": "Banner deleted successfully"}