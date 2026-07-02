import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.database import Base, get_db
from app.core.auth import create_access_token, hash_password
from app.main import app

# Use a test DB URL (SQLite in-memory for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def seed_admin_user(db_session):
    from app.models.user import User
    
    admin_user = User(
        email="admin@reputationos.ai",
        hashed_password=hash_password("adminpass123"),
        name="Admin User",
        role="super_admin",
        is_active=True
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)
    return admin_user


@pytest_asyncio.fixture
async def client(db_session):
    """FastAPI test client with overridden DB dependency."""
    from httpx import ASGITransport, AsyncClient

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpass123",
    }


@pytest.fixture
def test_user_token():
    return create_access_token(data={"sub": "test@example.com"})


@pytest.fixture
def admin_token():
    return create_access_token(data={"sub": "admin@reputationos.ai"})
