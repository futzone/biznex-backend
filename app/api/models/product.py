from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Table,
    Text,
    Float,
    Boolean,
    ForeignKey,
    BigInteger,
    func,
)
from sqlalchemy.orm import relationship
from app.core.models.base import Base
from sqlalchemy.dialects.postgresql import JSONB


banner_products = Table(
    'banner_products',
    Base.metadata,
    Column('banner_id', Integer, ForeignKey('banners.id'), primary_key=True),
    Column('product_variant_id', Integer, ForeignKey('product_variants.id'), primary_key=True)
)

promotion_product_variants = Table(
    'promotion_product_variants',
    Base.metadata,
    Column('promotion_id', Integer, ForeignKey('promotions.id')),
    Column('product_variant_id', Integer, ForeignKey('product_variants.id'))
)

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(JSONB, default={}, nullable=False)
    image = Column(String(255), nullable=True)
    description = Column(JSONB, default={}, nullable=True)

    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    subcategories = relationship("Subcategory", back_populates="category")
    warehouse = relationship("Warehouse", back_populates="categories")
    warehouse_categories = relationship("WarehouseCategory", back_populates="global_category")

    def __repr__(self):
        return f"<Category id={self.id} name={self.name}>"


class Subcategory(Base):
    __tablename__ = "subcategories"

    id = Column(Integer, primary_key=True)
    name = Column(JSONB, default={}, nullable=False)
    description = Column(JSONB, default={}, nullable=True)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category = relationship("Category", back_populates="subcategories")
    products = relationship("Product", back_populates="subcategory")
    warehouse_subcategories = relationship("WarehouseSubcategory", back_populates="subcategory")

    def __repr__(self):
        return f"<Subcategory id={self.id} name={self.name}>"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(JSONB, default={}, nullable=False)  # search name
    description = Column(JSONB, default={}, nullable=True)  # search description

    product_information_id = Column(
        Integer, ForeignKey("product_information.id"), nullable=False
    )
    product_information = relationship("ProductInformation", back_populates="products")

    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    warehouse = relationship("Warehouse", back_populates="products")

    subcategory_id = Column(Integer, ForeignKey("subcategories.id"), nullable=False)
    subcategory = relationship("Subcategory", back_populates="products")

    orders = relationship("OrderItem", back_populates="product")
    ratings = relationship(
        "Rating",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    wishlists = relationship(
        "Wishlist", back_populates="product",
        cascade="all, delete-orphan")
    variants = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    created_at = Column(DateTime, default=func.now())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Product id={self.id} name={self.name}>"


class ProductInformation(Base):
    __tablename__ = "product_information"

    id = Column(Integer, primary_key=True)
    product_type = Column(
        String(50), nullable=False
    )  # e.g. "clothes", "phone", "drinks"
    brand = Column(String(50), nullable=True)  # e.g. "Nike", "Apple"
    model_name = Column(String(50), nullable=True)  # e.g. "iPhone X", "Coca Cola"
    description = Column(
        JSONB, default={}, nullable=True
    )  # a general textual description

    attributes = Column(JSONB, nullable=True, default={})

    products = relationship("Product", back_populates="product_information")

    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    warehouse = relationship("Warehouse", back_populates="product_information")

    created_at = Column(DateTime, default=func.now())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ProductInformation id={self.id} type={self.product_type} brand={self.brand}>"


from sqlalchemy import Column, Integer, Text, ForeignKey, CheckConstraint, String
from sqlalchemy.orm import relationship
from app.core.models.base import Base


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True)

    rating = Column(
        Integer, CheckConstraint("rating >= 1 AND rating <= 5"), nullable=False
    )
    comment = Column(String, default="", nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="ratings")

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product", back_populates="ratings")

    pictures = relationship(
        "RatingPicture", back_populates="rating", cascade="all, delete-orphan"
    )

    created_at = Column(DateTime, default=func.now())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Rating id={self.id} rating={self.rating}>"


class RatingPicture(Base):
    __tablename__ = "rating_pictures"

    id = Column(Integer, primary_key=True)
    rating_id = Column(Integer, ForeignKey("ratings.id"), nullable=False)
    rating = relationship("Rating", back_populates="pictures")

    # path to the image file on disk
    image_path = Column(String(255), nullable=False)

    created_at = Column(DateTime, default=func.now())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<RatingPicture id={self.id} rating_id={self.rating_id}>"


class Wishlist(Base):
    __tablename__ = "wishlists"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="wishlists")

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product", back_populates="wishlists")

    created_at = Column(DateTime, default=func.now())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Wishlist id={self.id} user={self.user_id} product={self.product_id}>"


class Size(Base):
    __tablename__ = "sizes"

    id = Column(Integer, primary_key=True)
    size = Column(String(20), nullable=False)
    description = Column(JSONB, default={}, nullable=True)

    product_variants = relationship("ProductVariant", back_populates="size")

    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    warehouse = relationship("Warehouse", back_populates="sizes")

    created_at = Column(DateTime, default=func.now())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Size id={self.id} size={self.size}>"


class Color(Base):
    __tablename__ = "colors"

    id = Column(Integer, primary_key=True)
    name = Column(JSONB, default={}, nullable=False)
    hex_code = Column(String(9), nullable=False)

    product_variants = relationship("ProductVariant", back_populates="color")

    created_at = Column(DateTime, default=func.now())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Color id={self.id} name={self.name}>"


class Measure(Base):
    __tablename__ = "measures"

    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)

    product_variants = relationship("ProductVariant", back_populates="measure")

    created_at = Column(DateTime, default=func.now())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Measure id={self.id} name={self.name}>"


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True)
    barcode = Column(BigInteger, nullable=False, index=True, unique=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product", back_populates="variants")

    come_in_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    old_price = Column(Float, nullable=True)
    discount = Column(Float, nullable=True)
    is_main = Column(Boolean, default=False)
    amount = Column(Float, nullable=False)
    weight = Column(Float, nullable=True)

    color_id = Column(Integer, ForeignKey("colors.id", ondelete="SET NULL"), nullable=True)
    color = relationship("Color", back_populates="product_variants")

    size_id = Column(Integer, ForeignKey("sizes.id",  ondelete="SET NULL"), nullable=True)
    size = relationship("Size", back_populates="product_variants")
    promotions = relationship(
        "Promotion",
        secondary=promotion_product_variants,
        back_populates="product_variants"
    )

    measure_id = Column(Integer, ForeignKey("measures.id"), nullable=False)
    measure = relationship("Measure", back_populates="product_variants")

    images = relationship(
        "ProductImage", back_populates="product_variant", cascade="all, delete-orphan"
    )

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ProductVariant id={self.id} product_id={self.product_id}>"



class Promotion(Base):
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    discount = Column(Float, nullable=False)  # Discount percentage
    product_limit = Column(Integer, nullable=False)  # Number of products the promotion applies to
    is_active = Column(Boolean, default=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    warehouse = relationship("Warehouse", back_populates="promotions")
    
    # Many-to-many relationship with ProductVariant
    product_variants = relationship(
        "ProductVariant",
        secondary=promotion_product_variants,
        back_populates="promotions"
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Add relationship to ProductVariant model
ProductVariant.promotions = relationship(
    "Promotion",
    secondary=promotion_product_variants,
    back_populates="product_variants"
)

class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True)
    product_variant_id = Column(
        Integer, ForeignKey("product_variants.id"), nullable=False
    )
    product_variant = relationship("ProductVariant", back_populates="images")

    alt_text = Column(JSONB, default={}, nullable=True)
    image = Column(String(255), nullable=False)
    is_main = Column(Boolean, default=False)

    created_at = Column(DateTime, default=func.now())  # Yaratilgan vaqt
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ProductImage id={self.id} variant={self.product_variant_id}>"


class Banner(Base):
    __tablename__ = "banners"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=False)
    discount_percentage = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Banner va ProductVariant o'rtasidagi ko'p-ko'plik bog'lanish
    product_variants = relationship(
        "ProductVariant",
        secondary=banner_products,
        backref="banners"
    )
    
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Banner id={self.id} title={self.title}>"
    
    def apply_discount_to_products(self):
        """Bannerdagi barcha productlarga discount qo'llash"""
        for variant in self.product_variants:
            if not variant.old_price:
                variant.old_price = variant.current_price
            
            variant.discount = self.discount_percentage
            variant.current_price = variant.old_price * (1 - self.discount_percentage / 100)