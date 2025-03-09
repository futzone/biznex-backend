from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.models.enums import RevisionStatus

class CreateRevisionSchema(BaseModel):
    warehouse_id: int
    notes: Optional[str] = None

class RevisionItemCreate(BaseModel):
    barcode: str
    actual_quantity: float = Field(gt=0)
    notes: Optional[str] = None
    
class RevisionItemResponse(BaseModel):
    id: int
    barcode: str
    product_name: str
    color: Optional[str]
    size: Optional[str]
    actual_quantity: float
    system_quantity: float
    difference: float
    notes: Optional[str]
    scanned_at: datetime

    class Config:
        from_attributes = True

class RevisionResponse(BaseModel):
    id: int
    warehouse_id: int
    warehouse_name: str
    status: RevisionStatus
    created_at: datetime
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    created_by: int
    completed_by: Optional[int]
    cancelled_by: Optional[int]
    notes: Optional[str]
    items_count: int
    discrepancy_count: int

    class Config:
        from_attributes = True

    
class RevisionDetailResponse(RevisionResponse):
    items: List[RevisionItemResponse]