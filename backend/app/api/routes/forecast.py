import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.ml.forecast_engine import generate_forecast
from app.models.forecast import DemandForecast, ForecastResult
from app.models.product import Product
from app.models.sales import SalesItem, Sale
from app.models.user import User
from app.schemas.forecast import ForecastGenerateRequest, ForecastResponse, ForecastResultResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/forecast", tags=["Forecast"])


def _forecast_response(forecast: DemandForecast, db: Session) -> ForecastResponse:
    product = db.query(Product).filter(Product.id == forecast.product_id).first()
    results = sorted(forecast.results, key=lambda r: r.forecast_date)
    return ForecastResponse(
        id=forecast.id,
        product_id=forecast.product_id,
        product_name=product.name if product else None,
        horizon_days=forecast.horizon_days,
        model_type=forecast.model_type,
        confidence_score=forecast.confidence_score,
        mae=forecast.mae,
        rmse=forecast.rmse,
        status=forecast.status,
        notes=forecast.notes,
        created_at=forecast.created_at,
        results=[
            ForecastResultResponse(
                forecast_date=r.forecast_date,
                predicted_demand=r.predicted_demand,
                lower_bound=r.lower_bound,
                upper_bound=r.upper_bound,
                is_historical=r.is_historical,
            )
            for r in results
        ],
    )


@router.post("/generate", response_model=ForecastResponse)
def generate_product_forecast(
    data: ForecastGenerateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "manager")),
):
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    sales_records = (
        db.query(SalesItem.quantity, Sale.sale_date)
        .join(Sale)
        .filter(SalesItem.product_id == data.product_id)
        .all()
    )
    records = [{"quantity": r.quantity, "sale_date": r.sale_date} for r in sales_records]

    logger.info("Generating forecast for product %s, horizon %s days", data.product_id, data.horizon_days)
    result = generate_forecast(records, data.horizon_days)

    forecast = DemandForecast(
        product_id=data.product_id,
        horizon_days=data.horizon_days,
        model_type=result["model_type"],
        confidence_score=result["confidence_score"],
        mae=result["mae"],
        rmse=result["rmse"],
        status=result["status"],
        notes=result["notes"],
    )
    db.add(forecast)
    db.flush()

    for r in result["results"]:
        db.add(
            ForecastResult(
                forecast_id=forecast.id,
                forecast_date=r["forecast_date"],
                predicted_demand=r["predicted_demand"],
                lower_bound=r.get("lower_bound"),
                upper_bound=r.get("upper_bound"),
                is_historical=r.get("is_historical", False),
            )
        )

    db.commit()
    forecast = (
        db.query(DemandForecast)
        .options(joinedload(DemandForecast.results))
        .filter(DemandForecast.id == forecast.id)
        .first()
    )
    return _forecast_response(forecast, db)


@router.get("/{product_id}", response_model=ForecastResponse | None)
def get_product_forecast(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    forecast = (
        db.query(DemandForecast)
        .options(joinedload(DemandForecast.results))
        .filter(DemandForecast.product_id == product_id)
        .order_by(DemandForecast.created_at.desc())
        .first()
    )
    if not forecast:
        return None
    return _forecast_response(forecast, db)
