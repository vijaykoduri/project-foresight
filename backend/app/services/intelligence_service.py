"""Inventory intelligence and reorder recommendation calculations."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.forecast import DemandForecast, ReorderRecommendation, RiskLevel
from app.models.product import Product


def calculate_average_daily_demand(db: Session, product_id: int, days: int = 30) -> float:
    from app.models.sales import SalesItem, Sale
    from datetime import datetime, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items = (
        db.query(SalesItem)
        .join(Sale)
        .filter(SalesItem.product_id == product_id, Sale.sale_date >= cutoff)
        .all()
    )
    if not items:
        return 0.0
    total_qty = sum(i.quantity for i in items)
    return total_qty / days


def calculate_safety_stock(avg_demand: float, lead_time_days: int) -> int:
    """Safety stock = 1.5 * avg daily demand * sqrt(lead time)."""
    import math

    return max(0, int(math.ceil(1.5 * avg_demand * math.sqrt(max(lead_time_days, 1)))))


def get_forecast_demand(db: Session, product_id: int, days: int = 30) -> float:
    forecast = (
        db.query(DemandForecast)
        .filter(DemandForecast.product_id == product_id)
        .order_by(DemandForecast.created_at.desc())
        .first()
    )
    if not forecast or not forecast.results:
        avg = calculate_average_daily_demand(db, product_id)
        return avg * days

    future = [r for r in forecast.results if not r.is_historical][:days]
    if not future:
        avg = calculate_average_daily_demand(db, product_id)
        return avg * days
    return sum(r.predicted_demand for r in future)


def calculate_risk_level(product: Product, avg_demand: float, days_remaining: float) -> str:
    if product.current_stock <= 0:
        return RiskLevel.CRITICAL.value
    if days_remaining <= product.lead_time_days:
        return RiskLevel.HIGH.value
    if days_remaining <= product.lead_time_days * 2:
        return RiskLevel.MEDIUM.value
    if product.current_stock <= product.reorder_point:
        return RiskLevel.MEDIUM.value
    return RiskLevel.LOW.value


def calculate_days_remaining(current_stock: int, avg_demand: float) -> float:
    if avg_demand <= 0:
        return float("inf") if current_stock > 0 else 0.0
    return current_stock / avg_demand


def generate_reorder_recommendation(db: Session, product: Product) -> ReorderRecommendation:
    """
    Reorder Qty = max(0, expected_demand_during_lead_time + safety_stock - available_inventory)

    expected_demand_during_lead_time = avg_daily_demand * lead_time_days
    """
    avg_demand = calculate_average_daily_demand(db, product.id)
    forecast_demand = get_forecast_demand(db, product.id, product.lead_time_days)
    safety_stock = calculate_safety_stock(avg_demand, product.lead_time_days)
    expected_demand = avg_demand * product.lead_time_days
    available = product.current_stock
    recommended = max(0, int(expected_demand + safety_stock - available))

    days_remaining = calculate_days_remaining(product.current_stock, avg_demand)
    risk = calculate_risk_level(product, avg_demand, days_remaining)

    if product.current_stock <= 0:
        reason = f"Product is out of stock. Average daily demand is {avg_demand:.1f} units."
    elif product.current_stock <= product.reorder_point:
        reason = (
            f"Stock ({product.current_stock}) is at or below reorder point ({product.reorder_point}). "
            f"Estimated {days_remaining:.1f} days of inventory remaining."
        )
    elif recommended > 0:
        reason = (
            f"Projected demand during {product.lead_time_days}-day lead time requires reorder. "
            f"Safety stock target: {safety_stock} units."
        )
    else:
        reason = "Stock levels are adequate based on current demand patterns."

    existing = (
        db.query(ReorderRecommendation)
        .filter(
            ReorderRecommendation.product_id == product.id,
            ReorderRecommendation.status.in_(["pending", "acknowledged"]),
        )
        .first()
    )

    if existing:
        existing.current_stock = product.current_stock
        existing.average_demand = round(avg_demand, 2)
        existing.forecast_demand = round(forecast_demand, 2)
        existing.lead_time_days = product.lead_time_days
        existing.safety_stock = safety_stock
        existing.recommended_quantity = recommended
        existing.risk_level = risk
        existing.reason = reason
        return existing

    rec = ReorderRecommendation(
        product_id=product.id,
        current_stock=product.current_stock,
        average_demand=round(avg_demand, 2),
        forecast_demand=round(forecast_demand, 2),
        lead_time_days=product.lead_time_days,
        safety_stock=safety_stock,
        recommended_quantity=recommended,
        risk_level=risk,
        reason=reason,
        status="pending",
    )
    db.add(rec)
    return rec


def generate_all_recommendations(db: Session) -> list[ReorderRecommendation]:
    products = db.query(Product).filter(Product.status == "active").all()
    recs = []
    for product in products:
        if product.current_stock <= product.reorder_point or product.current_stock <= 0:
            recs.append(generate_reorder_recommendation(db, product))
    db.commit()
    return recs
