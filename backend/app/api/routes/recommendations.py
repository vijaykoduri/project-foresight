from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.forecast import ReorderRecommendation
from app.models.product import Product
from app.models.user import User
from app.schemas.forecast import RecommendationResponse, RecommendationUpdateRequest
from app.services.intelligence_service import generate_all_recommendations, generate_reorder_recommendation

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


def _rec_response(rec: ReorderRecommendation, db: Session) -> RecommendationResponse:
    product = db.query(Product).filter(Product.id == rec.product_id).first()
    return RecommendationResponse(
        id=rec.id,
        product_id=rec.product_id,
        product_name=product.name if product else None,
        product_sku=product.sku if product else None,
        current_stock=rec.current_stock,
        average_demand=rec.average_demand,
        forecast_demand=rec.forecast_demand,
        lead_time_days=rec.lead_time_days,
        safety_stock=rec.safety_stock,
        recommended_quantity=rec.recommended_quantity,
        risk_level=rec.risk_level,
        reason=rec.reason,
        status=rec.status,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
    )


@router.get("", response_model=list[RecommendationResponse])
def list_recommendations(
    status: str | None = None,
    risk_level: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(ReorderRecommendation).order_by(ReorderRecommendation.created_at.desc())
    if status:
        query = query.filter(ReorderRecommendation.status == status)
    if risk_level:
        query = query.filter(ReorderRecommendation.risk_level == risk_level)
    recs = query.all()
    return [_rec_response(r, db) for r in recs]


@router.post("/generate")
def generate_recommendations(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "manager", "user")),
):
    recs = generate_all_recommendations(db)
    return {"message": f"Generated {len(recs)} recommendations", "count": len(recs)}


@router.put("/{rec_id}", response_model=RecommendationResponse)
def update_recommendation(
    rec_id: int,
    data: RecommendationUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "manager", "user")),
):
    valid_statuses = {"pending", "acknowledged", "ordered", "dismissed"}
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    rec = db.query(ReorderRecommendation).filter(ReorderRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec.status = data.status
    db.commit()
    db.refresh(rec)
    return _rec_response(rec, db)
