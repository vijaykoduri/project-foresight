from datetime import datetime
from pydantic import BaseModel, Field


class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class SaleCreate(BaseModel):
    customer_name: str | None = None
    notes: str | None = None
    items: list[SaleItemCreate] = Field(min_length=1)


class SaleItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str | None = None
    product_sku: str | None = None
    quantity: int
    unit_price: float
    line_total: float

    model_config = {"from_attributes": True}


class SaleResponse(BaseModel):
    id: int
    sale_number: str
    customer_name: str | None = None
    total_amount: float
    total_units: int
    notes: str | None = None
    sale_date: datetime
    created_at: datetime
    items: list[SaleItemResponse]

    model_config = {"from_attributes": True}


class SaleListResponse(BaseModel):
    items: list[SaleResponse]
    total: int
    page: int
    page_size: int
    pages: int
