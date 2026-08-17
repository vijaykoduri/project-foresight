from datetime import date, datetime
from pydantic import BaseModel, Field


class ForecastGenerateRequest(BaseModel):
    product_id: int
    horizon_days: int = Field(default=30, ge=1, le=90)


class ForecastResultResponse(BaseModel):
    forecast_date: date
    predicted_demand: float
    lower_bound: float | None = None
    upper_bound: float | None = None
    is_historical: bool = False


class ForecastResponse(BaseModel):
    id: int
    product_id: int
    product_name: str | None = None
    horizon_days: int
    model_type: str
    confidence_score: float | None = None
    mae: float | None = None
    rmse: float | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    results: list[ForecastResultResponse]

    model_config = {"from_attributes": True}


class RecommendationResponse(BaseModel):
    id: int
    product_id: int
    product_name: str | None = None
    product_sku: str | None = None
    current_stock: int
    average_demand: float
    forecast_demand: float
    lead_time_days: int
    safety_stock: int
    recommended_quantity: int
    risk_level: str
    reason: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecommendationUpdateRequest(BaseModel):
    status: str = Field(description="pending, acknowledged, ordered, dismissed")


class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    message: str
    product_id: int | None = None
    product_name: str | None = None
    is_read: bool
    is_resolved: bool
    created_at: datetime
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
    page: int
    page_size: int
    pages: int
