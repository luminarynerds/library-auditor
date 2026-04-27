import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings


class TestScanAPI:
    @pytest.mark.asyncio
    async def test_health(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/health")
            assert resp.status_code == 200
            assert resp.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_create_scan_bad_code(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/scans", json={
                "library_name": "Test Library",
                "base_url": "https://example.org",
                "access_code": "WRONGCODE",
            })
            assert resp.status_code == 403
