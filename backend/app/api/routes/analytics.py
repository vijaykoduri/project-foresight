from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.product import Category, Product, Supplier
from app.models.sales import Sale, SalesItem
from app.models.user import User
from app.schemas.dashboard import AnalyticsSummaryResponse, AnalyticsTrendsResponse, ChartDataPoint

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def analytics_summary(
    days: int = Query(30, ge=7, le=365),
    category_id: int | None = None,
    product_id: int | None = None,
    supplier_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    current_start = now - timedelta(days=days)
    prior_start = current_start - timedelta(days=days)

    def _revenue_in_period(start, end):
        q = db.query(func.coalesce(func.sum(Sale.total_amount), 0)).filter(
            Sale.sale_date >= start, Sale.sale_date < end
        )
        if product_id:
            q = q.join(SalesItem).filter(SalesItem.product_id == product_id)
        return float(q.scalar() or 0)

    def _units_in_period(start, end):
        q = db.query(func.coalesce(func.sum(SalesItem.quantity), 0)).join(Sale).filter(
            Sale.sale_date >= start, Sale.sale_date < end
        )
        if product_id:
            q = q.filter(SalesItem.product_id == product_id)
        elif category_id:
            q = q.join(Product).filter(Product.category_id == category_id)
        elif supplier_id:
            q = q.join(Product).filter(Product.supplier_id == supplier_id)
        return int(q.scalar() or 0)

    current_revenue = _revenue_in_period(current_start, now)
    prior_revenue = _revenue_in_period(prior_start, current_start)
    current_units = _units_in_period(current_start, now)
    prior_units = _units_in_period(prior_start, current_start)

    revenue_growth = ((current_revenue - prior_revenue) / prior_revenue * 100) if prior_revenue else 0
    sales_growth = ((current_units - prior_units) / prior_units * 100) if prior_units else 0

    products = db.query(Product).filter(Product.status == "active").all()
    total_inventory_value = sum(float(p.cost_price) * p.current_stock for p in products)
    inventory_turnover = (current_revenue / total_inventory_value) if total_inventory_value else 0

    out_of_stock = sum(1 for p in products if p.current_stock <= 0)
    stockout_frequency = (out_of_stock / len(products) * 100) if products else 0

    total_sales_count = db.query(Sale).filter(Sale.sale_date >= current_start).count()
    avg_order = current_revenue / total_sales_count if total_sales_count else 0

    return AnalyticsSummaryResponse(
        sales_growth=round(sales_growth, 2),
        revenue_growth=round(revenue_growth, 2),
        inventory_turnover=round(inventory_turnover, 2),
        stockout_frequency=round(stockout_frequency, 2),
        total_revenue=round(current_revenue, 2),
        total_units=current_units,
        avg_order_value=round(avg_order, 2),
    )


@router.get("/trends", response_model=AnalyticsTrendsResponse)
def analytics_trends(
    days: int = Query(30, ge=7, le=365),
    category_id: int | None = None,
    product_id: int | None = None,
    supplier_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    sales = db.query(Sale).filter(Sale.sale_date >= cutoff).order_by(Sale.sale_date).all()
    demand_daily: dict[str, float] = {}
    revenue_daily: dict[str, float] = {}
    for s in sales:
        key = s.sale_date.strftime("%Y-%m-%d")
        revenue_daily[key] = revenue_daily.get(key, 0) + float(s.total_amount)
        demand_daily[key] = demand_daily.get(key, 0) + s.total_units

    demand_trend = [ChartDataPoint(label=k, value=v) for k, v in sorted(demand_daily.items())]
    revenue_trend = [ChartDataPoint(label=k, value=round(v, 2)) for k, v in sorted(revenue_daily.items())]

    cat_query = (
        db.query(Category.name, func.sum(SalesItem.line_total))
        .join(Product, Product.category_id == Category.id)
        .join(SalesItem, SalesItem.product_id == Product.id)
        .join(Sale)
        .filter(Sale.sale_date >= cutoff)
        .group_by(Category.name)
    )
    category_performance = [
        ChartDataPoint(label=name, value=round(float(rev or 0), 2)) for name, rev in cat_query.all()
    ]

    top_query = (
        db.query(Product.name, func.sum(SalesItem.quantity))
        .join(SalesItem)
        .join(Sale)
        .filter(Sale.sale_date >= cutoff)
        .group_by(Product.name)
        .order_by(func.sum(SalesItem.quantity).desc())
        .limit(10)
    )
    top_products = [ChartDataPoint(label=name, value=int(qty)) for name, qty in top_query.all()]

    low_query = (
        db.query(Product.name, func.sum(SalesItem.quantity))
        .join(SalesItem)
        .join(Sale)
        .filter(Sale.sale_date >= cutoff)
        .group_by(Product.name)
        .order_by(func.sum(SalesItem.quantity).asc())
        .limit(5)
    )
    low_performing = [ChartDataPoint(label=name, value=int(qty)) for name, qty in low_query.all()]

    supplier_query = (
        db.query(Supplier.name, func.sum(SalesItem.line_total))
        .join(Product, Product.supplier_id == Supplier.id)
        .join(SalesItem)
        .join(Sale)
        .filter(Sale.sale_date >= cutoff)
        .group_by(Supplier.name)
    )
    supplier_performance = [
        ChartDataPoint(label=name, value=round(float(rev or 0), 2)) for name, rev in supplier_query.all()
    ]

    return AnalyticsTrendsResponse(
        demand_trend=demand_trend,
        revenue_trend=revenue_trend,
        category_performance=sorted(category_performance, key=lambda x: x.value, reverse=True),
        top_products=top_products,
        low_performing_products=low_performing,
        supplier_performance=sorted(supplier_performance, key=lambda x: x.value, reverse=True),
    )
