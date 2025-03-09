from itertools import product
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api.models import Product
from app.api.repositories.auth import UserRepository
from app.api.repositories.product.product import ProductRepository
from app.api.schemas.product.product import MainProductResponseSchema, ProductResponseSchema
from app.core.databases.postgres import get_general_session
from app.api.models.product import ProductVariant, Wishlist
from app.api.schemas.product.wishlist import (
    WishlistCreateSchema,
    WishlistUpdateSchema,
    WishlistResponseSchema,
)


class WishlistRepository:
    def __init__(
        self,
        session: AsyncSession = Depends(get_general_session),
        product_repository: ProductRepository = Depends(),
    ):
        self.__session = session
        self.__product_repository = product_repository

    async def get_wishlists(self, user_id: int | None) -> WishlistResponseSchema:
        if user_id is not None:
            result = await self.__session.execute(
                select(Wishlist).where(Wishlist.user_id == user_id)
            )
        else:
            result = await self.__session.execute(select(Wishlist))

        items = result.scalars().all()

        res = [item.product_id for item in items] if items else []

        return WishlistResponseSchema(product_id=res)

    async def get_wishlist_by_id(
        self, wishlist_id: int
    ) -> Optional[WishlistResponseSchema]:
        result = await self.__session.execute(
            select(Wishlist).where(Wishlist.id == wishlist_id)
        )
        w = result.scalar_one_or_none()
        product_ids = w.product_id if isinstance(w.product_id, list) else [w.product_id] if w.product_id is not None else []
        if not w:
            return []
        return WishlistResponseSchema(product_id=product_ids)

    async def create_wishlist(
        self, data: WishlistCreateSchema
    ) -> WishlistResponseSchema:
        existing_wishlist = await self.__session.execute(
            select(Wishlist).where(
                Wishlist.user_id == data.user_id, Wishlist.product_id == data.product_id
            )
        )

        if existing_wishlist.scalar_one_or_none():
            raise HTTPException(
                status_code=409, detail="This product is already in the wishlist"
            )

        wishlist_obj = Wishlist(**data.model_dump())
        self.__session.add(wishlist_obj)
        await self.__session.commit()
        await self.__session.refresh(wishlist_obj)

        return WishlistResponseSchema(product_id=[wishlist_obj.product_id])

    async def update_wishlist(
        self, wishlist_id: int, data: WishlistUpdateSchema
    ) -> WishlistResponseSchema:
        result = await self.__session.execute(
            select(Wishlist).where(Wishlist.id == wishlist_id)
        )
        w = result.scalar_one_or_none()
        if not w:
            raise HTTPException(404, "Wishlist not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(w, field, value)

        self.__session.add(w)
        await self.__session.commit()
        await self.__session.refresh(w)
        return WishlistResponseSchema.model_validate(w)

    async def delete_wishlist(self, product_id: int, user_id: int) -> None:
        result = await self.__session.execute(
            select(Wishlist).where(
                Wishlist.user_id == user_id, Wishlist.product_id.in_([
                                                                     product_id])
            )
        )

        wishlists = result.scalars().all()

        if wishlists:
            for wishlist in wishlists:
                if isinstance(wishlist.product_id, list):
                    if product_id in wishlist.product_id:
                        wishlist.product_id.remove(product_id)
                else:
                    if wishlist.product_id == product_id:
                        wishlist.product_id = None

                if not wishlist.product_id:
                    await self.__session.delete(wishlist)
                else:
                    self.__session.add(wishlist)

            await self.__session.commit()

    async def get_wishlist_products(self, user_id, language):
        result = await self.__session.execute(
            select(Wishlist).where(Wishlist.user_id == user_id).options(
                selectinload(Wishlist.product),
                selectinload(Wishlist.product).selectinload(Product.variants).selectinload(ProductVariant.images),
                selectinload(Wishlist.product).selectinload(Product.ratings),
                selectinload(Wishlist.product).selectinload(Product.product_information),
                selectinload(Wishlist.product).selectinload(Product.variants).selectinload(ProductVariant.color),
                selectinload(Wishlist.product).selectinload(Product.variants).selectinload(ProductVariant.size),
                selectinload(Wishlist.product).selectinload(Product.subcategory),
            )
        )

        wishlists = result.scalars().all()
        products = []

        for wishlist in wishlists:
            if wishlist.product:
                product_response = await self.__product_repository._build_product_response(wishlist.product, language)
                products.append(product_response)

        return products
