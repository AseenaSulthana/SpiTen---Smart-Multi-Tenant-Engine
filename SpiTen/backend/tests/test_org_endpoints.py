import pytest
import httpx
from httpx import AsyncClient
from app.main import app
from app.database import connect_to_mongo, close_mongo_connection, get_master_db
import asyncio

@pytest.fixture(scope="session")
async def test_client():
    """Create test client"""
    await connect_to_mongo()
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    await close_mongo_connection()

@pytest.mark.asyncio
async def test_create_organization(test_client):
    """Test organization creation"""
    response = await test_client.post("/org/create", json={
        "organization_name": "testorg",
        "email": "test@testorg.com",
        "password": "TestPass123!"
    })
    assert response.status_code == 201
    assert response.json()["data"]["organization_name"] == "testorg"

@pytest.mark.asyncio
async def test_get_organization(test_client):
    """Test getting organization"""
    response = await test_client.get("/org/get", params={"organization_name": "testorg"})
    assert response.status_code == 200
    assert response.json()["data"]["organization_name"] == "testorg"

@pytest.mark.asyncio
async def test_admin_login(test_client):
    """Test admin login"""
    response = await test_client.post("/admin/login", json={
        "email": "test@testorg.com",
        "password": "TestPass123!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]
