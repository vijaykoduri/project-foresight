import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProductStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"


class StockStatus(str, enum.Enum):
    HEALTHY = "healthy"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    OVERSTOCK = "overstock"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    contact_person: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    products: Mapped[list["Product"]] = relationship("Product", back_populates="supplier")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    cost_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    minimum_stock: Mapped[int] = mapped_column(Integer, default=10)
    maximum_stock: Mapped[int] = mapped_column(Integer, default=500)
    reorder_point: Mapped[int] = mapped_column(Integer, default=20)
    reorder_quantity: Mapped[int] = mapped_column(Integer, default=50)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    category: Mapped["Category"] = relationship("Category", back_populates="products")
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="products")
    inventory_records: Mapped[list["Inventory"]] = relationship(
        "Inventory", back_populates="product", uselist=True
    )
    sales_items: Mapped[list["SalesItem"]] = relationship("SalesItem", back_populates="product")
    transactions: Mapped[list["InventoryTransaction"]] = relationship(
        "InventoryTransaction", back_populates="product"
    )
    forecasts: Mapped[list["DemandForecast"]] = relationship(
        "DemandForecast", back_populates="product"
    )
    recommendations: Mapped[list["ReorderRecommendation"]] = relationship(
        "ReorderRecommendation", back_populates="product"
    )
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="product")

    @property
    def stock_status(self) -> str:
        if self.current_stock <= 0:
            return StockStatus.OUT_OF_STOCK.value
        if self.current_stock <= self.reorder_point:
            return StockStatus.LOW_STOCK.value
        if self.current_stock >= self.maximum_stock:
            return StockStatus.OVERSTOCK.value
        return StockStatus.HEALTHY.value
