from typing import List
from fastapi import Depends, HTTPException, status

from app.api.repositories.product.product import ProductRepository
from app.api.repositories.product.wishlist import WishlistRepository
from app.api.repositories.user import UserRepository
from app.api.schemas.product.wishlist import (
    WishlistCreateSchema,
    WishlistUpdateSchema,
    WishlistResponseSchema,
)


class WishlistController:
    def __init__(
        self,
        repo: WishlistRepository = Depends(),
        user_repository: UserRepository = Depends(),
        product_repository: ProductRepository = Depends(),
    ):
        self.__repo = repo
        self.__user_repository = user_repository
        self.__product_repository = product_repository

    async def get_wishlists(self, user_id: int | None) -> WishlistResponseSchema:
        if user_id is not None:
            user = await self.__user_repository.get_user_by_id(user_id)
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
        return await self.__repo.get_wishlists(user_id)

    async def get_wishlist_by_id(self, wishlist_id: int):
        wishlist = await self.__repo.get_wishlist_by_id(wishlist_id)
        if not wishlist:
            raise HTTPException(404, "Wishlist not found")
        return wishlist

    async def create_wishlist(
        self, data: WishlistCreateSchema
    ) -> WishlistResponseSchema:
        if await self.__user_repository.get_user_by_id(data.user_id) is None:
            raise HTTPException(404, "User not found")
        if await self.__product_repository.get_product_by_id(data.product_id) is None:
            raise HTTPException(404, "Product not found")
        return await self.__repo.create_wishlist(data)

    async def update_wishlist(
        self, wishlist_id: int, data: WishlistUpdateSchema
    ) -> WishlistResponseSchema:
        return await self.__repo.update_wishlist(wishlist_id, data)

    async def delete_wishlist(self, product_id: int, user_id: int) -> None:
        return await self.__repo.delete_wishlist(product_id, user_id)

    async def get_wishlist_products(self, user_id: int, language="uz"):
        if await self.__user_repository.get_user_by_id(user_id) is None:
            raise HTTPException(404, "User not found")
        return await self.__repo.get_wishlist_products(user_id, language)
