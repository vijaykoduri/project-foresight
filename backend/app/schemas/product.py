from datetime import datetime
from pydantic import BaseModel, Field


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class SupplierBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    lead_time_days: int = Field(default=7, ge=0)
    status: str = "active"


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: str | None = None
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    lead_time_days: int | None = Field(default=None, ge=0)
    status: str | None = None


class SupplierResponse(SupplierBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category_id: int
    supplier_id: int
    unit_price: float = Field(gt=0)
    cost_price: float = Field(gt=0)
    current_stock: int = Field(default=0, ge=0)
    minimum_stock: int = Field(default=10, ge=0)
    maximum_stock: int = Field(default=500, ge=0)
    reorder_point: int = Field(default=20, ge=0)
    reorder_quantity: int = Field(default=50, ge=0)
    lead_time_days: int = Field(default=7, ge=0)
    status: str = "active"


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: str | None = None
    name: str | None = None
    description: str | None = None
    category_id: int | None = None
    supplier_id: int | None = None
    unit_price: float | None = Field(default=None, gt=0)
    cost_price: float | None = Field(default=None, gt=0)
    current_stock: int | None = Field(default=None, ge=0)
    minimum_stock: int | None = Field(default=None, ge=0)
    maximum_stock: int | None = Field(default=None, ge=0)
    reorder_point: int | None = Field(default=None, ge=0)
    reorder_quantity: int | None = Field(default=None, ge=0)
    lead_time_days: int | None = Field(default=None, ge=0)
    status: str | None = None


class ProductResponse(ProductBase):
    id: int
    stock_status: str
    category: CategoryResponse
    supplier: SupplierResponse
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    pages: int
