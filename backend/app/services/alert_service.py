"""Alert generation service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.forecast import Alert, AlertSeverity, AlertType
from app.models.product import Product
from app.services.intelligence_service import calculate_average_daily_demand, calculate_days_remaining


def _create_alert_if_new(
    db: Session,
    alert_type: str,
    severity: str,
    message: str,
    product_id: int | None = None,
) -> Alert | None:
    existing = (
        db.query(Alert)
        .filter(
            Alert.alert_type == alert_type,
            Alert.product_id == product_id,
            Alert.is_resolved == False,  # noqa: E712
        )
        .first()
    )
    if existing:
        return None

    alert = Alert(
        alert_type=alert_type,
        severity=severity,
        message=message,
        product_id=product_id,
    )
    db.add(alert)
    return alert


def generate_alerts(db: Session) -> list[Alert]:
    alerts: list[Alert] = []
    products = db.query(Product).filter(Product.status == "active").all()

    for product in products:
        if product.current_stock <= 0:
            a = _create_alert_if_new(
                db,
                AlertType.OUT_OF_STOCK.value,
                AlertSeverity.CRITICAL.value,
                f"{product.name} ({product.sku}) is out of stock.",
                product.id,
            )
            if a:
                alerts.append(a)
        elif product.current_stock <= product.reorder_point:
            a = _create_alert_if_new(
                db,
                AlertType.LOW_STOCK.value,
                AlertSeverity.WARNING.value,
                f"{product.name} ({product.sku}) is low on stock: {product.current_stock} units remaining.",
                product.id,
            )
            if a:
                alerts.append(a)
        elif product.current_stock >= product.maximum_stock:
            a = _create_alert_if_new(
                db,
                AlertType.OVERSTOCK.value,
                AlertSeverity.INFO.value,
                f"{product.name} ({product.sku}) is overstocked with {product.current_stock} units.",
                product.id,
            )
            if a:
                alerts.append(a)

        avg_demand = calculate_average_daily_demand(db, product.id)
        if avg_demand > 0:
            days_remaining = calculate_days_remaining(product.current_stock, avg_demand)
            if days_remaining <= product.lead_time_days and product.current_stock > 0:
                a = _create_alert_if_new(
                    db,
                    AlertType.PROJECTED_STOCKOUT.value,
                    AlertSeverity.CRITICAL.value,
                    f"{product.name} may stock out in ~{days_remaining:.0f} days based on current demand.",
                    product.id,
                )
                if a:
                    alerts.append(a)

        recent_avg = calculate_average_daily_demand(db, product.id, days=7)
        prior_avg = calculate_average_daily_demand(db, product.id, days=30)
        if prior_avg > 0 and recent_avg > prior_avg * 1.5:
            a = _create_alert_if_new(
                db,
                AlertType.UNUSUAL_DEMAND_INCREASE.value,
                AlertSeverity.WARNING.value,
                f"Unusual demand increase detected for {product.name}: +{((recent_avg/prior_avg)-1)*100:.0f}% vs baseline.",
                product.id,
            )
            if a:
                alerts.append(a)
        elif prior_avg > 0 and recent_avg < prior_avg * 0.5 and recent_avg > 0:
            a = _create_alert_if_new(
                db,
                AlertType.UNUSUAL_DEMAND_DECREASE.value,
                AlertSeverity.INFO.value,
                f"Demand decrease detected for {product.name}: {((recent_avg/prior_avg)-1)*100:.0f}% vs baseline.",
                product.id,
            )
            if a:
                alerts.append(a)

    db.commit()
    return alerts
