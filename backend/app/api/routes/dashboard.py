from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.forecast import Alert, DemandForecast, ForecastResult, ReorderRecommendation
from app.models.inventory import InventoryTransaction
from app.models.product import Product
from app.models.sales import Sale, SalesItem
from app.models.user import User
from app.schemas.dashboard import ChartDataPoint, DashboardSummaryResponse, KPICard, TrendResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    products = db.query(Product).filter(Product.status == "active").all()
    total_revenue = float(db.query(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0)
    total_sales = db.query(Sale).count()
    units_sold = int(db.query(func.coalesce(func.sum(Sale.total_units), 0)).scalar() or 0)
    inventory_value = sum(float(p.cost_price) * p.current_stock for p in products)

    low_stock = sum(1 for p in products if p.stock_status == "low_stock")
    out_of_stock = sum(1 for p in products if p.stock_status == "out_of_stock")
    overstock = sum(1 for p in products if p.stock_status == "overstock")

    forecast_demand = 0.0
    latest_forecasts = (
        db.query(DemandForecast)
        .order_by(DemandForecast.created_at.desc())
        .limit(10)
        .all()
    )
    for f in latest_forecasts:
        future = [r for r in f.results if not r.is_historical]
        forecast_demand += sum(r.predicted_demand for r in future[:7])

    kpis = [
        KPICard(label="Total Revenue", value=round(total_revenue, 2), format="currency"),
        KPICard(label="Total Sales", value=total_sales, format="number"),
        KPICard(label="Units Sold", value=units_sold, format="number"),
        KPICard(label="Inventory Value", value=round(inventory_value, 2), format="currency"),
        KPICard(label="Low Stock Items", value=low_stock, format="number"),
        KPICard(label="Out of Stock", value=out_of_stock, format="number"),
        KPICard(label="Overstock Items", value=overstock, format="number"),
        KPICard(label="7-Day Forecast Demand", value=round(forecast_demand, 0), format="number"),
    ]

    return DashboardSummaryResponse(
        total_revenue=round(total_revenue, 2),
        total_sales=total_sales,
        units_sold=units_sold,
        inventory_value=round(inventory_value, 2),
        low_stock_items=low_stock,
        out_of_stock_items=out_of_stock,
        overstock_items=overstock,
        forecasted_demand=round(forecast_demand, 2),
        kpis=kpis,
    )


@router.get("/revenue", response_model=TrendResponse)
def revenue_trend(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    sales = (
        db.query(Sale)
        .filter(Sale.sale_date >= cutoff)
        .order_by(Sale.sale_date)
        .all()
    )
    daily: dict[str, float] = {}
    for s in sales:
        key = s.sale_date.strftime("%Y-%m-%d")
        daily[key] = daily.get(key, 0) + float(s.total_amount)

    data = [ChartDataPoint(label=k, value=round(v, 2)) for k, v in sorted(daily.items())]
    return TrendResponse(data=data)


@router.get("/sales", response_model=TrendResponse)
def sales_trend(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    sales = db.query(Sale).filter(Sale.sale_date >= cutoff).order_by(Sale.sale_date).all()
    daily: dict[str, float] = {}
    for s in sales:
        key = s.sale_date.strftime("%Y-%m-%d")
        daily[key] = daily.get(key, 0) + s.total_units

    data = [ChartDataPoint(label=k, value=v) for k, v in sorted(daily.items())]
    return TrendResponse(data=data)


@router.get("/inventory", response_model=TrendResponse)
def inventory_trend(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    products = db.query(Product).filter(Product.status == "active").all()
    status_counts = {"healthy": 0, "low_stock": 0, "out_of_stock": 0, "overstock": 0}
    for p in products:
        status_counts[p.stock_status] = status_counts.get(p.stock_status, 0) + 1

    labels = {
        "healthy": "Healthy",
        "low_stock": "Low Stock",
        "out_of_stock": "Out of Stock",
        "overstock": "Overstock",
    }
    data = [ChartDataPoint(label=labels[k], value=v) for k, v in status_counts.items()]
    return TrendResponse(data=data)


@router.get("/category-performance", response_model=TrendResponse)
def category_performance(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    results = (
        db.query(Product.category_id, func.sum(SalesItem.line_total).label("revenue"))
        .join(SalesItem, SalesItem.product_id == Product.id)
        .group_by(Product.category_id)
        .all()
    )
    from app.models.product import Category

    data = []
    for cat_id, revenue in results:
        cat = db.query(Category).filter(Category.id == cat_id).first()
        if cat:
            data.append(ChartDataPoint(label=cat.name, value=round(float(revenue or 0), 2)))
    return TrendResponse(data=sorted(data, key=lambda x: x.value, reverse=True))


@router.get("/top-products", response_model=TrendResponse)
def top_products(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    results = (
        db.query(SalesItem.product_id, func.sum(SalesItem.quantity).label("qty"))
        .group_by(SalesItem.product_id)
        .order_by(func.sum(SalesItem.quantity).desc())
        .limit(limit)
        .all()
    )
    data = []
    for product_id, qty in results:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            data.append(ChartDataPoint(label=product.name, value=int(qty)))
    return TrendResponse(data=data)


@router.get("/recent-alerts")
def recent_alerts(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    alerts = (
        db.query(Alert)
        .filter(Alert.is_resolved == False)  # noqa: E712
        .order_by(Alert.created_at.desc())
        .limit(5)
        .all()
    )
    return [
        {
            "id": a.id,
            "type": a.alert_type,
            "severity": a.severity,
            "message": a.message,
            "product_id": a.product_id,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]


@router.get("/reorder-items")
def reorder_items(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    recs = (
        db.query(ReorderRecommendation)
        .filter(ReorderRecommendation.status.in_(["pending", "acknowledged"]))
        .order_by(ReorderRecommendation.risk_level.desc())
        .limit(5)
        .all()
    )
    result = []
    for r in recs:
        product = db.query(Product).filter(Product.id == r.product_id).first()
        result.append(
            {
                "id": r.id,
                "product_id": r.product_id,
                "product_name": product.name if product else None,
                "recommended_quantity": r.recommended_quantity,
                "risk_level": r.risk_level,
            }
        )
    return result


@router.get("/recent-transactions")
def recent_transactions(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    txs = (
        db.query(InventoryTransaction)
        .order_by(InventoryTransaction.created_at.desc())
        .limit(10)
        .all()
    )
    result = []
    for t in txs:
        product = db.query(Product).filter(Product.id == t.product_id).first()
        result.append(
            {
                "id": t.id,
                "product_name": product.name if product else None,
                "transaction_type": t.transaction_type,
                "quantity_change": t.quantity_change,
                "created_at": t.created_at.isoformat(),
            }
        )
    return result
