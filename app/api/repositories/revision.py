from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.models.product import Product, ProductVariant
from app.api.models.revision import Revision, RevisionItem
from app.api.models.user import AdminUser
from app.api.schemas.revision import CreateRevisionSchema, RevisionItemResponse
from app.core.models.enums import RevisionStatus



class RevisionRepository:
    def __init__(self, session: AsyncSession):
        self.__session = session

    async def get_active_revision(self, warehouse_id: int) -> Optional[Revision]:
        query = (
            select(Revision)
            .where(
                and_(
                    Revision.warehouse_id == warehouse_id,
                    Revision.status == RevisionStatus.created
                )
            )
            .options(
                selectinload(Revision.warehouse),
                selectinload(Revision.items).selectinload(RevisionItem.product_variant)
            )
        )
        result = await self.__session.execute(query)
        return result.scalar_one_or_none()

    async def create_revision(self, warehouse_id: int, admin_id: int, notes: Optional[str] = None) -> Revision:
        current_revision = await self.get_active_revision(warehouse_id)
        if current_revision:
            raise HTTPException(
                status_code=400,
                detail="There is already an active revision for this warehouse"
                )
        revision = Revision(
            warehouse_id=warehouse_id,
            created_by=admin_id,
            notes=notes
        )
        self.__session.add(revision)
        await self.__session.commit()
        
        query = (
            select(Revision)
            .where(Revision.id == revision.id)
            .options(
                selectinload(Revision.warehouse),
                selectinload(Revision.items)
            )
        )
        result = await self.__session.execute(query)
        return result.scalar_one()
        
    async def get_product_variant_by_barcode(self, barcode: str, warehouse_id: int):
        query = (
            select(ProductVariant)
            .join(Product)
            .where(
                and_(
                    ProductVariant.barcode == barcode,
                    Product.warehouse_id == warehouse_id
                )
            )
            .options(
                selectinload(ProductVariant.product),
                selectinload(ProductVariant.color),
                selectinload(ProductVariant.size)
            )
        )
        result = await self.__session.execute(query)
        return result.scalar_one_or_none()
    

    async def create_or_update_revision_item(
        self,
        revision_id: int,
        product_variant_id: int,
        actual_quantity: float,
        system_quantity: float,
        notes: Optional[str] = None
    ) -> RevisionItem:
        query = (
            select(RevisionItem)
            .where(
                and_(
                    RevisionItem.revision_id == revision_id,
                    RevisionItem.product_variant_id == product_variant_id
                )
            )
        )
        result = await self.__session.execute(query)
        item = result.scalar_one_or_none()

        if item:
            item.actual_quantity = actual_quantity
            item.difference = actual_quantity - system_quantity
            item.notes = notes
            item.scanned_at = datetime.utcnow()
        else:
            item = RevisionItem(
                revision_id=revision_id,
                product_variant_id=product_variant_id,
                system_quantity=system_quantity,
                actual_quantity=actual_quantity,
                difference=actual_quantity - system_quantity,
                notes=notes
            )
            self.__session.add(item)

        await self.__session.commit()
        await self.__session.refresh(item)
        return item

    async def get_revision_with_items(self, revision_id: int) -> Optional[Revision]:
        query = (
            select(Revision)
            .where(Revision.id == revision_id)
            .options(
                selectinload(Revision.warehouse),
                selectinload(Revision.items)
                .selectinload(RevisionItem.product_variant)
                .selectinload(ProductVariant.product),
                selectinload(Revision.items)
                .selectinload(RevisionItem.product_variant)
                .selectinload(ProductVariant.color),
                selectinload(Revision.items)
                .selectinload(RevisionItem.product_variant)
                .selectinload(ProductVariant.size)
            )
        )
        result = await self.__session.execute(query)
        return result.scalar_one_or_none()

    async def complete_revision(self, revision_id: int, admin_id: int) -> Revision:
        revision = await self.get_revision_with_items(revision_id)
        if not revision:
            return None

        for item in revision.items:
            variant = item.product_variant
            variant.amount = item.actual_quantity

        revision.status = RevisionStatus.completed
        revision.completed_at = datetime.utcnow()
        revision.completed_by = admin_id

        await self.__session.commit()
        await self.__session.refresh(revision)
        return revision

    async def cancel_revision(self, revision_id: int, admin_id: int) -> Revision:
        revision = await self.get_revision_with_items(revision_id)
        if not revision:
            return None

        revision.status = RevisionStatus.cancelled
        revision.cancelled_at = datetime.utcnow()
        revision.cancelled_by = admin_id

        await self.__session.commit()
        await self.__session.refresh(revision)
        return revision

    async def get_revision_statistics(self, revision_id: int):
        query = (
            select(
                func.count(RevisionItem.id).label("total_items"),
                func.count(RevisionItem.id).filter(RevisionItem.difference != 0).label("discrepancy_count"),
                func.sum(RevisionItem.difference).label("total_difference")
            )
            .where(RevisionItem.revision_id == revision_id)
        )
        result = await self.__session.execute(query)
        return result.first()

    async def get_revisions_by_warehouse(
        self,
        warehouse_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[Revision]:
        query = (
            select(Revision)
            .where(Revision.warehouse_id == warehouse_id)
            .options(
                selectinload(Revision.warehouse),
                selectinload(Revision.creator),
                selectinload(Revision.completer),
                selectinload(Revision.canceller)
            )
            .order_by(Revision.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.__session.execute(query)
        return result.scalars().all()