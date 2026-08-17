from datetime import date
from pydantic import BaseModel


class KPICard(BaseModel):
    label: str
    value: float | int | str
    change: float | None = None
    format: str = "number"


class ChartDataPoint(BaseModel):
    label: str
    value: float
    value2: float | None = None


class DashboardSummaryResponse(BaseModel):
    total_revenue: float
    total_sales: int
    units_sold: int
    inventory_value: float
    low_stock_items: int
    out_of_stock_items: int
    overstock_items: int
    forecasted_demand: float
    kpis: list[KPICard]


class TrendResponse(BaseModel):
    data: list[ChartDataPoint]


class AnalyticsSummaryResponse(BaseModel):
    sales_growth: float
    revenue_growth: float
    inventory_turnover: float
    stockout_frequency: float
    total_revenue: float
    total_units: int
    avg_order_value: float


class AnalyticsTrendsResponse(BaseModel):
    demand_trend: list[ChartDataPoint]
    revenue_trend: list[ChartDataPoint]
    category_performance: list[ChartDataPoint]
    top_products: list[ChartDataPoint]
    low_performing_products: list[ChartDataPoint]
    supplier_performance: list[ChartDataPoint]
