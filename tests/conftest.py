import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.database import get_async_session
from src.cache.redis_client import cache_get, cache_set, cache_delete

import src.cache.redis_client


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """
    Фикстура мока redis.
    """
    fake_redis = MagicMock()
    fake_redis.get = AsyncMock(return_value=None)
    fake_redis.set = AsyncMock()
    fake_redis.delete = AsyncMock()

    monkeypatch.setattr(src.cache.redis_client, "get_redis_client", lambda: fake_redis)


@pytest.fixture
def mock_db_session():
    """
    Фикстура мока базы данных.
    """
    mock = MagicMock()

    # Асинхронные методы
    mock.commit = AsyncMock()
    mock.refresh = AsyncMock()
    mock.execute = AsyncMock()
    mock.delete = AsyncMock()

    # Синхронные методы
    mock.add = MagicMock()

    # Прочие функции
    fake_execute_result = MagicMock()
    fake_scalars = MagicMock()
    fake_scalars.all.return_value = []
    fake_scalars.first.return_value = None
    fake_execute_result.scalars.return_value = fake_scalars
    mock.execute = AsyncMock(return_value=fake_execute_result)

    return mock


@pytest.fixture(autouse=True)
def override_db_dependency(mock_db_session):
    """
    Фикстура асинхронных сессий, используемых в endpoints.
    """
    app.dependency_overrides[get_async_session] = lambda: mock_db_session


@pytest_asyncio.fixture
async def async_client():
    """
    Фикстура асинхронного клиента.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client