import logging

from app.core.logging_config import setup_logging
from app.db.base import Base
from app.db.session import engine
from app.models import (
    Alert,
    Category,
    DemandForecast,
    ForecastResult,
    Inventory,
    InventoryTransaction,
    Product,
    ReorderRecommendation,
    Role,
    Sale,
    SalesItem,
    Supplier,
    User,
)

logger = logging.getLogger(__name__)


def init_db() -> None:
    setup_logging()
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


if __name__ == "__main__":
    init_db()
