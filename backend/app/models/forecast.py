import enum
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), default="linear_regression")
    confidence_score: Mapped[float | None] = mapped_column(Float)
    mae: Mapped[float | None] = mapped_column(Float)
    rmse: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30), default="completed")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    product: Mapped["Product"] = relationship("Product", back_populates="forecasts")
    results: Mapped[list["ForecastResult"]] = relationship(
        "ForecastResult", back_populates="forecast", cascade="all, delete-orphan"
    )


class ForecastResult(Base):
    __tablename__ = "forecast_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("demand_forecasts.id"), nullable=False, index=True
    )
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    predicted_demand: Mapped[float] = mapped_column(Float, nullable=False)
    lower_bound: Mapped[float | None] = mapped_column(Float)
    upper_bound: Mapped[float | None] = mapped_column(Float)
    is_historical: Mapped[bool] = mapped_column(default=False)

    forecast: Mapped["DemandForecast"] = relationship("DemandForecast", back_populates="results")


class RecommendationStatus(str, enum.Enum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    ORDERED = "ordered"
    DISMISSED = "dismissed"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReorderRecommendation(Base):
    __tablename__ = "reorder_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    current_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    average_demand: Mapped[float] = mapped_column(Float, default=0)
    forecast_demand: Mapped[float] = mapped_column(Float, default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)
    safety_stock: Mapped[int] = mapped_column(Integer, default=0)
    recommended_quantity: Mapped[int] = mapped_column(Integer, default=0)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    product: Mapped["Product"] = relationship("Product", back_populates="recommendations")


class AlertType(str, enum.Enum):
    OUT_OF_STOCK = "out_of_stock"
    LOW_STOCK = "low_stock"
    PROJECTED_STOCKOUT = "projected_stockout"
    UNUSUAL_DEMAND_INCREASE = "unusual_demand_increase"
    UNUSUAL_DEMAND_DECREASE = "unusual_demand_decrease"
    OVERSTOCK = "overstock"
    FORECAST_RISK = "forecast_risk"
    INVENTORY_ANOMALY = "inventory_anomaly"


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), index=True)
    is_read: Mapped[bool] = mapped_column(default=False, index=True)
    is_resolved: Mapped[bool] = mapped_column(default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    product: Mapped["Product | None"] = relationship("Product", back_populates="alerts")
