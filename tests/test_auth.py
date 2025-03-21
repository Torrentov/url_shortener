import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import uuid


@pytest.mark.asyncio
async def test_signup_and_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Signup
        unique = str(uuid.uuid4())[:8]
        user = {"email": f"{unique}@test.com", "password": "secret"}
        res = await ac.post("/auth/signup", json=user)
        assert res.status_code == 200

        # 2. Login
        res = await ac.post("/auth/login", json=user)
        assert res.status_code == 200
