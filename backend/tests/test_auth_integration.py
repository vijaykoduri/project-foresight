import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.user import User

client = TestClient(app)

def test_admin_login():
    response = client.post("/api/auth/login", json={
        "email": "admin@foresight.local",
        "password": "Admin@12345"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    token = data["access_token"]
    
    # Decode token and check claims
    claims = decode_access_token(token)
    assert claims is not None
    assert claims.get("role") == "admin"

def test_manager_login():
    response = client.post("/api/auth/login", json={
        "email": "manager@foresight.local",
        "password": "Manager@12345"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    token = data["access_token"]
    
    # Decode token and check claims
    claims = decode_access_token(token)
    assert claims is not None
    assert claims.get("role") == "manager"

def test_invalid_credentials():
    response = client.post("/api/auth/login", json={
        "email": "admin@foresight.local",
        "password": "WrongPassword"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_admin_only_endpoint_protection():
    # Login as manager
    response = client.post("/api/auth/login", json={
        "email": "manager@foresight.local",
        "password": "Manager@12345"
    })
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to access admin-only list users
    users_resp = client.get("/api/users", headers=headers)
    assert users_resp.status_code == 403
    
    # Login as admin
    admin_response = client.post("/api/auth/login", json={
        "email": "admin@foresight.local",
        "password": "Admin@12345"
    })
    admin_token = admin_response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Access list users
    admin_users_resp = client.get("/api/users", headers=admin_headers)
    assert admin_users_resp.status_code == 200

def test_manager_and_user_core_permissions():
    # Clean up test user if exists
    db = SessionLocal()
    existing = db.query(User).filter(User.email == "test_core_perm@example.com").first()
    if existing:
        db.delete(existing)
        db.commit()
    db.close()

    # Register normal user
    reg_resp = client.post("/api/auth/register", json={
        "email": "test_core_perm@example.com",
        "full_name": "Test Core Perm",
        "password": "Password@12345"
    })
    assert reg_resp.status_code == 201
    
    # Login normal user
    login_resp = client.post("/api/auth/login", json={
        "email": "test_core_perm@example.com",
        "password": "Password@12345"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Adjust stock (should succeed)
    adjust_resp = client.post("/api/inventory/adjust", headers=headers, json={
        "product_id": 1,
        "quantity_change": 1,
        "transaction_type": "incoming",
        "reference": "TEST-PERM",
        "notes": "Testing standard user permission"
    })
    assert adjust_resp.status_code == 200
