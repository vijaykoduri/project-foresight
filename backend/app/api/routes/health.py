from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import engine, get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    settings = get_settings()
    db_status = "connected"
    tables = []
    try:
        db.execute(text("SELECT 1"))
        if engine.dialect.name == "sqlite":
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        else:
            query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
        result = db.execute(text(query))
        tables = [row[0] for row in result.fetchall()]
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": db_status,
        "tables_count": len(tables),
        "tables": tables[:20],
    }
