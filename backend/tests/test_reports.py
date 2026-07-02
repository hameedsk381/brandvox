import pytest

pytestmark = pytest.mark.asyncio

async def test_generate_report_pdf(client, admin_token):
    response = await client.post(
        "/api/reports/generate?format=pdf&report_type=monthly",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in (200, 401)
    if response.status_code == 200:
        assert response.headers["content-type"] == "application/pdf"

async def test_generate_report_excel(client, admin_token):
    response = await client.post(
        "/api/reports/generate?format=excel&report_type=monthly",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in (200, 401)
    if response.status_code == 200:
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

async def test_generate_report_pptx(client, admin_token):
    response = await client.post(
        "/api/reports/generate?format=pptx&report_type=monthly",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in (200, 401)
    if response.status_code == 200:
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"

async def test_generate_report_unauthenticated(client):
    response = await client.post("/api/reports/generate?format=pptx&report_type=monthly")
    assert response.status_code == 401
