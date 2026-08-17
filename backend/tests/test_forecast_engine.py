import pytest
from datetime import datetime, timedelta
from app.ml.forecast_engine import generate_forecast

def test_generate_forecast_fallback():
    # Create less than 14 days of history to trigger fallback logic
    sales = [
        {"quantity": 5, "sale_date": (datetime.now() - timedelta(days=i)).isoformat()}
        for i in range(5)
    ]
    result = generate_forecast(sales, horizon_days=7)
    
    assert result["model_type"] == "historical_average_fallback"
    assert result["status"] == "completed"
    assert result["confidence_score"] == 0.5
    assert len(result["results"]) > 0
    
    # Check prediction result keys
    first_res = result["results"][0]
    assert "forecast_date" in first_res
    assert "predicted_demand" in first_res
    assert "is_historical" in first_res

def test_generate_forecast_ml():
    # Create 20 days of history to trigger scikit-learn ML logic
    sales = [
        {"quantity": 10 + (i % 3), "sale_date": (datetime.now() - timedelta(days=i)).isoformat()}
        for i in range(20)
    ]
    result = generate_forecast(sales, horizon_days=14)
    
    assert result["model_type"] == "linear_regression"
    assert result["status"] == "completed"
    assert result["confidence_score"] >= 0.0
    assert result["confidence_score"] <= 1.0
    assert result["mae"] is not None
    assert result["rmse"] is not None
    assert len(result["results"]) > 0
