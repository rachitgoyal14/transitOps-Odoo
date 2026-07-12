import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from typing import AsyncGenerator

import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app
from app.core.config import settings
from app.db.session import get_db

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    # Create engine inside the fixture to ensure it binds to the current test event loop
    engine = create_async_engine(settings.DATABASE_URL, connect_args={"ssl": "require"}, echo=False)
    async with engine.connect() as conn:
        # Begin transaction
        transaction = await conn.begin()
        # Create session bound to connection
        async with AsyncSession(bind=conn, expire_on_commit=False) as session:
            yield session
            # Rollback transaction at end of test
            await transaction.rollback()
    await engine.dispose()

@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
