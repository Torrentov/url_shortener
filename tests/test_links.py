import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import Base, engine, SessionLocal
import uuid
from datetime import datetime, timezone


@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_create_redirect_update_delete_link_authorized():
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
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Create
        res = await ac.post("/links/shorten", json={"original_url": "https://example.com/"}, headers=headers)
        assert res.status_code == 200
        short_code = res.json()["short_code"]

        # 4. Redirect
        res = await ac.get(f"/links/{short_code}", follow_redirects=False)
        assert res.status_code == 307
        assert res.headers["location"] == "https://example.com/"

        # 5. Update
        res = await ac.put(f"/links/{short_code}", json={"original_url": "https://updated.com/"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["original_url"] == "https://updated.com/"

        # 6. Redirect again
        res = await ac.get(f"/links/{short_code}", follow_redirects=False)
        assert res.status_code == 307
        assert res.headers["location"] == "https://updated.com/"

        # 7. Delete
        res = await ac.delete(f"/links/{short_code}", headers=headers)
        assert res.status_code == 200

        # 8. Verify deletion
        res = await ac.get(f"/links/{short_code}")
        assert res.status_code == 404

@pytest.mark.asyncio
async def test_create_redirect_anon():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/links/shorten", json={"original_url": "https://anon.com/"})
        assert res.status_code == 200
        short_code = res.json()["short_code"]

        res = await ac.get(f"/links/{short_code}", follow_redirects=False)
        assert res.status_code == 307
        assert res.headers["location"] == "https://anon.com/"

@pytest.mark.asyncio
async def test_custom_alias():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        unique = str(uuid.uuid4())[:8]
        res = await ac.post("/links/shorten", json={"original_url": "https://customalias.com/", "custom_alias": unique})
        assert res.status_code == 200
        short_code = res.json()["short_code"]
        assert short_code == unique

        res = await ac.get(f"/links/{short_code}", follow_redirects=False)
        assert res.status_code == 307
        assert res.headers["location"] == "https://customalias.com/"

@pytest.mark.asyncio
async def test_expires_at():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        expires_at_dt = datetime.now(timezone.utc)
        expires_at = expires_at_dt.isoformat(timespec="microseconds")
        res = await ac.post("/links/shorten", json={"original_url": "https://expiresat.com/", "expires_at": expires_at})
        assert res.status_code == 200
        short_code = res.json()["short_code"]
        returned_expires_at = datetime.fromisoformat(res.json()["expires_at"])
        assert returned_expires_at.replace(tzinfo=None) == expires_at_dt.replace(tzinfo=None)

        res = await ac.get(f"/{short_code}", follow_redirects=False)
        assert res.status_code == 404

        res = await ac.post("/links/shorten", json={"original_url": "https://expiresat.com/", "expires_at": expires_at, "custom_alias": short_code})
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_link_stats_and_search(test_db: Session):
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
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Create
        res = await ac.post("/links/shorten", json={"original_url": "https://statssearch.com/"}, headers=headers)
        assert res.status_code == 200
        short_code = res.json()["short_code"]

        # 4. Stats
        response = await ac.get(f"/links/{short_code}/stats")
        assert response.status_code == 200
        assert response.json()["original_url"] == "https://statssearch.com/"

        # 5. Search
        response = await ac.get("/links/search", params={
            "original_url": "https://statssearch.com/"
        })
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]["short_code"] == short_code

        # 6. Delete
        res = await ac.delete(f"/links/{short_code}", headers=headers)
        assert res.status_code == 200

        # 7. Verify deletion
        res = await ac.get(f"/links/{short_code}")
        assert res.status_code == 404

