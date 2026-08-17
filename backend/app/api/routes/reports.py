import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.forecast import DemandForecast, ReorderRecommendation
from app.models.product import Product
from app.models.sales import Sale, SalesItem
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["Reports"])


def _csv_response(filename: str, rows: list[list], headers: list[str]):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/inventory")
def inventory_report(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    products = db.query(Product).filter(Product.status == "active").all()
    rows = []
    for p in products:
        rows.append([
            p.sku, p.name, p.category.name if p.category else "",
            p.supplier.name if p.supplier else "",
            p.current_stock, p.reorder_point, p.minimum_stock, p.maximum_stock,
            float(p.unit_price), float(p.cost_price),
            round(float(p.cost_price) * p.current_stock, 2), p.stock_status,
        ])
    return _csv_response(
        f"inventory_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv",
        rows,
        ["SKU", "Name", "Category", "Supplier", "Stock", "Reorder Point",
         "Min Stock", "Max Stock", "Unit Price", "Cost Price", "Inventory Value", "Status"],
    )


@router.get("/sales")
def sales_report(
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    sales = (
        db.query(Sale)
        .options(joinedload(Sale.items))
        .filter(Sale.sale_date >= cutoff)
        .order_by(Sale.sale_date.desc())
        .all()
    )
    rows = []
    for s in sales:
        for item in s.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            rows.append([
                s.sale_number, s.sale_date.strftime("%Y-%m-%d"),
                s.customer_name or "", product.name if product else "",
                item.quantity, float(item.unit_price), float(item.line_total),
            ])
    return _csv_response(
        f"sales_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv",
        rows,
        ["Sale Number", "Date", "Customer", "Product", "Quantity", "Unit Price", "Line Total"],
    )


@router.get("/forecast")
def forecast_report(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    forecasts = (
        db.query(DemandForecast)
        .options(joinedload(DemandForecast.results))
        .order_by(DemandForecast.created_at.desc())
        .limit(50)
        .all()
    )
    rows = []
    for f in forecasts:
        product = db.query(Product).filter(Product.id == f.product_id).first()
        for r in f.results:
            if not r.is_historical:
                rows.append([
                    product.name if product else f.product_id,
                    f.horizon_days, f.model_type,
                    r.forecast_date.isoformat(), r.predicted_demand,
                    r.lower_bound or "", r.upper_bound or "",
                    f.confidence_score or "",
                ])
    return _csv_response(
        f"forecast_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv",
        rows,
        ["Product", "Horizon Days", "Model", "Date", "Predicted Demand",
         "Lower Bound", "Upper Bound", "Confidence"],
    )


@router.get("/reorder")
def reorder_report(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    recs = db.query(ReorderRecommendation).order_by(ReorderRecommendation.created_at.desc()).all()
    rows = []
    for r in recs:
        product = db.query(Product).filter(Product.id == r.product_id).first()
        rows.append([
            product.name if product else r.product_id,
            product.sku if product else "",
            r.current_stock, r.average_demand, r.forecast_demand,
            r.lead_time_days, r.safety_stock, r.recommended_quantity,
            r.risk_level, r.status, r.reason or "",
        ])
    return _csv_response(
        f"reorder_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv",
        rows,
        ["Product", "SKU", "Current Stock", "Avg Demand", "Forecast Demand",
         "Lead Time", "Safety Stock", "Recommended Qty", "Risk", "Status", "Reason"],
    )
