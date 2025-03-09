# app/api/routers/product/wishlist.py
from typing import List
from fastapi import APIRouter, Depends, Header, status, HTTPException

from app.api.controllers.product.wishlist import WishlistController
from app.api.schemas.product.wishlist import (
    WishlistCreateSchema,
    WishlistUpdateSchema,
    WishlistResponseSchema,
)
from app.api.utils.user import AuthUtils

router = APIRouter()


@router.get("/", response_model=WishlistResponseSchema, status_code=status.HTTP_200_OK)
async def get_wishlists(
    current_user: dict = Depends(AuthUtils.get_current_user_from_cookie),
    controller: WishlistController = Depends()
):
    return await controller.get_wishlists(int(current_user.get("sub")))


@router.get(
    "/{wishlist_id}/",
    response_model=WishlistResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_wishlist(wishlist_id: int, controller: WishlistController = Depends()):
    return await controller.get_wishlist_by_id(wishlist_id)


@router.post(
    "/", response_model=WishlistResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_wishlist(
    data: WishlistCreateSchema, controller: WishlistController = Depends()
):
    return await controller.create_wishlist(data)


@router.put("/{wishlist_id}/", response_model=WishlistResponseSchema, status_code=status.HTTP_200_OK,)
async def update_wishlist(
    wishlist_id: int,
    data: WishlistUpdateSchema,
    controller: WishlistController = Depends(),
):
    return await controller.update_wishlist(wishlist_id, data)


@router.delete("/{product_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wishlist(
    product_id: int, user_id: int, controller: WishlistController = Depends()
):
    await controller.delete_wishlist(product_id, user_id)


@router.get("/products", status_code=status.HTTP_200_OK)
async def get_wishlist_products(
    current_user: dict = Depends(AuthUtils.get_current_user_from_cookie),
    language: str = Header(None, alias="language"),
    controller: WishlistController = Depends()
):
    return await controller.get_wishlist_products(int(current_user.get("sub")), language)
