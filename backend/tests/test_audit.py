import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant import Agency
from app.models.user import User
from app.services.audit_service import audit_service
from app.core.auth import create_access_token

@pytest.mark.asyncio
async def test_audit_log_creation_and_retrieval(client: AsyncClient, db_session: AsyncSession):
    # Setup test data
    from app.models.tenant import Agency
    from app.models.user import User
    from app.core.auth import hash_password
    import uuid
    
    test_agency = Agency(name="Test Agency", slug=f"test-{uuid.uuid4()}")
    db_session.add(test_agency)
    await db_session.flush()
    
    test_user = User(
        email="test_audit@example.com",
        hashed_password=hash_password("password"),
        name="Test Audit User",
        role="agency_admin",
        agency_id=test_agency.id
    )
    db_session.add(test_user)
    await db_session.commit()

    # 1. Create an audit log via service
    await audit_service.log_action(
        db=db_session,
        agency_id=test_agency.id,
        action="test.action",
        resource_type="TestResource",
        resource_id="123",
        user_id=test_user.id,
        details={"key": "value"}
    )

    
    # 2. Retrieve via API
    # Create token for test_user (assuming test_user is an agency_admin)
    token = create_access_token({"sub": test_user.email})
    
    response = await client.get(
        "/api/audit",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    
    # Check that our test log is there
    test_log = next((log for log in data if log["action"] == "test.action"), None)
    assert test_log is not None
    assert test_log["resource_type"] == "TestResource"
    assert test_log["details"] == {"key": "value"}
    assert test_log["user_name"] == test_user.name
