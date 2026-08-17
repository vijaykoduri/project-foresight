from datetime import datetime
from pydantic import BaseModel, Field


class InventoryAdjustRequest(BaseModel):
    product_id: int
    quantity_change: int = Field(description="Positive for incoming, negative for outgoing")
    transaction_type: str = "adjustment"
    notes: str | None = None
    reference: str | None = None


class InventoryTransactionResponse(BaseModel):
    id: int
    product_id: int
    product_name: str | None = None
    product_sku: str | None = None
    transaction_type: str
    quantity_change: int
    quantity_before: int
    quantity_after: int
    reference: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InventoryItemResponse(BaseModel):
    product_id: int
    sku: str
    name: str
    category_name: str
    current_stock: int
    minimum_stock: int
    maximum_stock: int
    reorder_point: int
    unit_price: float
    cost_price: float
    inventory_value: float
    stock_status: str


class InventorySummaryResponse(BaseModel):
    total_inventory_value: float
    total_products: int
    low_stock_count: int
    out_of_stock_count: int
    overstock_count: int
    healthy_stock_count: int
    items: list[InventoryItemResponse]
