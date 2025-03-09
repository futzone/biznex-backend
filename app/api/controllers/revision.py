from typing import Optional

from fastapi import HTTPException
from app.api.repositories.revision import RevisionRepository
from app.api.schemas.revision import CreateRevisionSchema, RevisionItemCreate, RevisionItemResponse, RevisionResponse, RevisionDetailResponse
from sqlalchemy.ext.asyncio import AsyncSession


class RevisionController:
    def __init__(self, session: AsyncSession):
        self.__session = session
        self.repository = RevisionRepository(self.__session)

    
    async def get_active_revision(self, warehouse_id: int) -> Optional[RevisionResponse]:
        revision = await self.repository.get_active_revision(warehouse_id)
        if revision is None:
            return None
        
        return RevisionResponse(
            id=revision.id,
            warehouse_id=revision.warehouse_id,
            warehouse_name=revision.warehouse.name,
            status=revision.status,
            created_at=revision.created_at,
            completed_at=revision.completed_at,
            cancelled_at=revision.cancelled_at,
            created_by=revision.created_by,
            completed_by=revision.completed_by,
            cancelled_by=revision.cancelled_by,
            notes=revision.notes,
            items_count=len(revision.items),
            discrepancy_count=sum(1 for item in revision.items if item.difference != 0)
        )
    
    async def create_revision(self, schema: CreateRevisionSchema, admin_id: int) -> RevisionResponse:
        revision = await self.repository.create_revision(schema.warehouse_id, admin_id, schema.notes)
        return RevisionResponse(
            id=revision.id,
            warehouse_id=revision.warehouse_id,
            warehouse_name=revision.warehouse.name,
            status=revision.status,
            created_at=revision.created_at,
            completed_at=revision.completed_at,
            cancelled_at=revision.cancelled_at,
            created_by=revision.created_by,
            completed_by=revision.completed_by,
            cancelled_by=revision.cancelled_by,
            notes=revision.notes,
            items_count=len(revision.items),
            discrepancy_count=sum(1 for item in revision.items if item.difference != 0)
        )
    
    async def get_revision_detail(self, revision_id: int) -> Optional[RevisionDetailResponse]:
        revision = await self.repository.get_revision_with_items(revision_id)
        if revision is None:
            return None

        items = [
            RevisionItemResponse(
                id=item.id,
                barcode=item.product_variant.barcode,
                product_name=item.product_variant.product.name,
                color=item.product_variant.color.name if item.product_variant.color else None,
                size=item.product_variant.size.name if item.product_variant.size else None,
                actual_quantity=item.actual_quantity,
                system_quantity=item.system_quantity,
                difference=item.difference,
                notes=item.notes,
                scanned_at=item.scanned_at
            )
            for item in revision.items
        ]

        return RevisionDetailResponse(
            id=revision.id,
            warehouse_id=revision.warehouse_id,
            warehouse_name=revision.warehouse.name,
            status=revision.status,
            created_at=revision.created_at,
            completed_at=revision.completed_at,
            cancelled_at=revision.cancelled_at,
            created_by=revision.created_by,
            completed_by=revision.completed_by,
            cancelled_by=revision.cancelled_by,
            notes=revision.notes,
            items_count=len(revision.items),
            discrepancy_count=sum(1 for item in revision.items if item.difference != 0),
            items=items
        )

    async def add_revision_item(self, revision_id: int, warehouse_id: int, schema: RevisionItemCreate) -> RevisionItemResponse:
        variant = await self.repository.get_product_variant_by_barcode(schema.barcode, warehouse_id)
        if not variant:
            raise HTTPException(status_code=404, detail="Product variant not found")

        item = await self.repository.create_or_update_revision_item(
            revision_id=revision_id,
            product_variant_id=variant.id,
            actual_quantity=schema.actual_quantity,
            system_quantity=variant.amount,
            notes=schema.notes
        )

        return RevisionItemResponse(
            id=item.id,
            barcode=variant.barcode,
            product_name=variant.product.name,
            color=variant.color.name if variant.color else None,
            size=variant.size.name if variant.size else None,
            actual_quantity=item.actual_quantity,
            system_quantity=item.system_quantity,
            difference=item.difference,
            notes=item.notes,
            scanned_at=item.scanned_at
        )

    async def complete_revision(self, revision_id: int, admin_id: int) -> RevisionResponse:
        revision = await self.repository.complete_revision(revision_id, admin_id)
        if not revision:
            raise HTTPException(status_code=404, detail="Revision not found")
        
        return RevisionResponse(
            id=revision.id,
            warehouse_id=revision.warehouse_id,
            warehouse_name=revision.warehouse.name,
            status=revision.status,
            created_at=revision.created_at,
            completed_at=revision.completed_at,
            cancelled_at=revision.cancelled_at,
            created_by=revision.created_by,
            completed_by=revision.completed_by,
            cancelled_by=revision.cancelled_by,
            notes=revision.notes,
            items_count=len(revision.items),
            discrepancy_count=sum(1 for item in revision.items if item.difference != 0)
        )

    async def cancel_revision(self, revision_id: int, admin_id: int) -> RevisionResponse:
        revision = await self.repository.cancel_revision(revision_id, admin_id)
        if not revision:
            raise HTTPException(status_code=404, detail="Revision not found")
        
        return RevisionResponse(
            id=revision.id,
            warehouse_id=revision.warehouse_id,
            warehouse_name=revision.warehouse.name,
            status=revision.status,
            created_at=revision.created_at,
            completed_at=revision.completed_at,
            cancelled_at=revision.cancelled_at,
            created_by=revision.created_by,
            completed_by=revision.completed_by,
            cancelled_by=revision.cancelled_by,
            notes=revision.notes,
            items_count=len(revision.items),
            discrepancy_count=sum(1 for item in revision.items if item.difference != 0)
        )