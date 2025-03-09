from typing import List, Sequence, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.constants.languages import languages_error_message, languages
from app.api.utils.translator import translate_text
from app.core.databases.postgres import get_general_session
from app.api.models.product import ProductInformation
from app.api.schemas.product.product_information import (
    ProductInformationCreateSchema,
    ProductInformationUpdateSchema,
    ProductInformationResponseSchema,
    ProductInformationLanguageResponseSchema,
)


class ProductInformationRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.__session = session

    async def get_all_info(
            self, warehouse_id: int | None, language: str | None
    ) -> Sequence[
        ProductInformationResponseSchema | ProductInformationLanguageResponseSchema
        ]:
        if warehouse_id is not None:
            result = await self.__session.execute(
                select(ProductInformation).where(
                    ProductInformation.warehouse_id == warehouse_id
                )
            )
        else:
            result = await self.__session.execute(select(ProductInformation))

        infos = result.scalars().all()
        if language is None:
            return [
                ProductInformationLanguageResponseSchema.model_validate(i)
                for i in infos
            ]
        return [
            ProductInformationResponseSchema(
                id=i.id,
                warehouse_id=i.warehouse_id,
                product_type=i.product_type,
                brand=i.brand,
                model_name=i.model_name,
                description=i.description.get(language),
                attributes=i.attributes,
            )
            for i in infos
        ]

    async def get_info_by_warehouse_id(
            self, warehouse_id: int
    ) -> List[ProductInformationResponseSchema]:
        result = await self.__session.execute(
            select(ProductInformation).where(
                ProductInformation.warehouse_id == warehouse_id
            )
        )
        infos = result.scalars().all()
        return [ProductInformationResponseSchema.model_validate(i) for i in infos]

    async def get_info_by_id(
            self, info_id: int, language: str | None = None
    ) -> Optional[
        ProductInformationResponseSchema | ProductInformationLanguageResponseSchema
        ]:
        result = await self.__session.execute(
            select(ProductInformation).where(ProductInformation.id == info_id)
        )
        info = result.scalar_one_or_none()
        if not info:
            return None
        if language is not None:
            prd_info = ProductInformationResponseSchema(
                id=info.id,
                warehouse_id=info.warehouse_id,
                product_type=info.product_type,
                brand=info.brand,
                model_name=info.model_name,
                description=info.description.get(language),
                attributes=info.attributes,
            )
            return ProductInformationResponseSchema.model_validate(prd_info)
        return ProductInformationLanguageResponseSchema.model_validate(info)

    async def create_info(
            self, data: ProductInformationCreateSchema
    ) -> ProductInformationLanguageResponseSchema:
        data = data.model_dump()
        data["description"] = await translate_text(data["description"]) if data["description"] else {}
        info_instance = ProductInformation(**data)
        self.__session.add(info_instance)
        await self.__session.commit()
        await self.__session.refresh(info_instance)
        return ProductInformationLanguageResponseSchema.model_validate(info_instance)

    async def update_info(
            self, info_id: int, data: ProductInformationUpdateSchema
    ) -> ProductInformationLanguageResponseSchema:
        result = await self.__session.execute(
            select(ProductInformation).where(ProductInformation.id == info_id)
        )
        info = result.scalar_one_or_none()

        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ProductInformation not found",
            )

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(info, key, value)

        self.__session.add(info)
        await self.__session.commit()
        await self.__session.refresh(info)
        return ProductInformationLanguageResponseSchema.model_validate(info)

    async def delete_info(self, info_id: int) -> None:
        result = await self.__session.execute(
            select(ProductInformation).where(ProductInformation.id == info_id)
        )
        info = result.scalar_one_or_none()
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ProductInformation not found",
            )

        await self.__session.delete(info)
        await self.__session.commit()
