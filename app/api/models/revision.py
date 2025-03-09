from datetime import datetime
from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM

from app.core.models.base import Base
from app.core.models.enums import RevisionStatus



class Revision(Base):
    __tablename__ = "revisions"
    
    id = Column(Integer, primary_key=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    status = Column(ENUM(RevisionStatus), default=RevisionStatus.created)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("admin_users.id"), nullable=False)
    completed_by = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    cancelled_by = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    notes = Column(String, nullable=True)
    
    # Relationships
    items = relationship("RevisionItem", back_populates="revision", cascade="all, delete-orphan")
    warehouse = relationship("Warehouse", back_populates="revisions")
    creator = relationship("AdminUser", foreign_keys=[created_by])
    completer = relationship("AdminUser", foreign_keys=[completed_by])
    canceller = relationship("AdminUser", foreign_keys=[cancelled_by])


class RevisionItem(Base):
    __tablename__ = "revision_items"
    
    id = Column(Integer, primary_key=True)
    revision_id = Column(Integer, ForeignKey("revisions.id"), nullable=False)
    product_variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
    system_quantity = Column(Numeric(10, 2), nullable=False)
    actual_quantity = Column(Numeric(10, 2), nullable=False)
    difference = Column(Numeric(10, 2), nullable=False)
    notes = Column(String, nullable=True)
    scanned_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    revision = relationship("Revision", back_populates="items")
    product_variant = relationship("ProductVariant")