import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.forecast import Alert
from app.models.product import Product
from app.models.user import User
from app.schemas.forecast import AlertListResponse, AlertResponse
from app.services.alert_service import generate_alerts

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _alert_response(alert: Alert, db: Session) -> AlertResponse:
    product_name = None
    if alert.product_id:
        product = db.query(Product).filter(Product.id == alert.product_id).first()
        product_name = product.name if product else None
    return AlertResponse(
        id=alert.id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        message=alert.message,
        product_id=alert.product_id,
        product_name=product_name,
        is_read=alert.is_read,
        is_resolved=alert.is_resolved,
        created_at=alert.created_at,
        resolved_at=alert.resolved_at,
    )


@router.get("", response_model=AlertListResponse)
def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: str | None = None,
    is_read: bool | None = None,
    is_resolved: bool | None = None,
    alert_type: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Alert)
    if severity:
        query = query.filter(Alert.severity == severity)
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)
    if is_resolved is not None:
        query = query.filter(Alert.is_resolved == is_resolved)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)

    total = query.count()
    pages = max(1, math.ceil(total / page_size))
    alerts = (
        query.order_by(Alert.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return AlertListResponse(
        items=[_alert_response(a, db) for a in alerts],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("/generate")
def trigger_alert_generation(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "manager", "user")),
):
    alerts = generate_alerts(db)
    return {"message": f"Generated {len(alerts)} new alerts", "count": len(alerts)}


@router.put("/{alert_id}/read", response_model=AlertResponse)
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return _alert_response(alert, db)


@router.put("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_resolved = True
    alert.is_read = True
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return _alert_response(alert, db)
