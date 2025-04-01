from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Float,
    ForeignKey,
    Table,
    Text,
    Enum,
    UniqueConstraint,
    Boolean,
    func,
)
from sqlalchemy.orm import relationship
from app.core.models.base import Base
from app.core.models.enums import WarehouseApplicationStatus
from sqlalchemy.dialects.postgresql import JSONB

from utils.time_utils import now_time

admin_warehouse_roles = Table(
    "admin_warehouse_roles",
    Base.metadata,
    Column(
        "admin_id",
        Integer,
        ForeignKey("admin_users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "warehouse_role_id",
        Integer,
        ForeignKey("admin_warehouses.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("admin_id", "warehouse_role_id", name="uix_admin_role"),
)


class AdminWarehouse(Base):
    __tablename__ = "admin_warehouses"

    id = Column(Integer, primary_key=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    name = Column(String(255), nullable=False)
    is_owner = Column(Boolean, default=False)
    permissions = Column(JSONB, nullable=False)

    # Relationships
    admins = relationship(
        "AdminUser", secondary=admin_warehouse_roles, back_populates="warehouse_roles"
    )
    warehouse = relationship("Warehouse", back_populates="roles")

    created_at = Column(DateTime, default=now_time())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=now_time(), onupdate=now_time())


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    owner_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False)
    owner_phone_number = Column(String(15), nullable=True, unique=False)

    revisions = relationship("Revision", back_populates="warehouse")

    # Relationships
    roles = relationship(
        "AdminWarehouse", back_populates="warehouse", cascade="all, delete-orphan"
    )
    promotions = relationship("Promotion", back_populates="warehouse")
    products = relationship("Product", back_populates="warehouse")
    owner = relationship("AdminUser", foreign_keys=[owner_id])
    warehouse_applications = relationship(
        "WarehouseApplication", back_populates="warehouse", cascade="all, delete-orphan"
    )
    categories = relationship("Category", back_populates="warehouse")
    sizes = relationship("Size", back_populates="warehouse")
    admin_order = relationship("AdminOrder", back_populates="warehouse")
    product_information = relationship(
        "ProductInformation", back_populates="warehouse")
    warehouse_subcategories = relationship("WarehouseSubcategory", back_populates="warehouse")
    warehouse_categories = relationship("WarehouseCategory", back_populates="warehouse")

    created_at = Column(DateTime, default=now_time())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=now_time(), onupdate=now_time())

    @property
    def subcategories(self):
        """Returns all subcategories associated with this warehouse"""
        return [ws.subcategory for ws in self.warehouse_subcategories if ws.is_active]

    def __repr__(self):
        return f"<Warehouse id={self.id} name={self.name}>"

class WarehouseCategory(Base):
    __tablename__ = "warehouse_categories"

    id = Column(Integer, primary_key=True)
    name = Column(JSONB, default={}, nullable=False)  # Customizable name for this warehouse
    description = Column(JSONB, default={}, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Foreign keys
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    global_category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    
    # Relationships
    warehouse = relationship("Warehouse", back_populates="warehouse_categories")
    global_category = relationship("Category", back_populates="warehouse_categories")
    warehouse_subcategories = relationship("WarehouseSubcategory", back_populates="warehouse_category")
    
    # Prevent duplicates
    __table_args__ = (
        UniqueConstraint('warehouse_id', 'global_category_id', name='uq_warehouse_category'),
    )
    
    def __repr__(self):
        return f"<WarehouseCategory id={self.id} warehouse_id={self.warehouse_id} global_category_id={self.global_category_id}>"

class WarehouseSubcategory(Base):
    __tablename__ = "warehouse_subcategories"

    id = Column(Integer, primary_key=True)
    name = Column(JSONB, default={}, nullable=False)
    description = Column(JSONB, default={}, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id"), nullable=False)
    warehouse_category_id = Column(Integer, ForeignKey("warehouse_categories.id"), nullable=False)
    
    warehouse = relationship("Warehouse", back_populates="warehouse_subcategories")
    subcategory = relationship("Subcategory", back_populates="warehouse_subcategories")
    warehouse_category = relationship("WarehouseCategory", back_populates="warehouse_subcategories")
    
    __table_args__ = (
        UniqueConstraint('warehouse_id', 'subcategory_id', name='uq_warehouse_subcategory'),
    )
    
    def __repr__(self):
        return f"<WarehouseSubcategory id={self.id} warehouse_id={self.warehouse_id} subcategory_id={self.subcategory_id}>"

class WarehouseApplication(Base):
    __tablename__ = "warehouse_applications"

    id = Column(Integer, primary_key=True)
    phone_number = Column(String(15), nullable=False)
    bank_account = Column(String(20), nullable=False)
    image = Column(String(100), nullable=True)
    status = Column(
        Enum(WarehouseApplicationStatus, name="warehouseapplicationstatus"),
        nullable=False,
        default=WarehouseApplicationStatus.PENDING.value,
    )
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)

    # Relationship
    warehouse = relationship(
        "Warehouse", back_populates="warehouse_applications")

    created_at = Column(DateTime, default=now_time())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=now_time(), onupdate=now_time())

    def __repr__(self):
        return f"<WarehouseApplication id={self.id} phone_number={self.phone_number} status={self.status}>"