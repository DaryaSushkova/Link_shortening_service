import pytest
from unittest.mock import MagicMock

from src.main import app
from src.auth.manager import current_active_user


@pytest.mark.asyncio
async def test_create_short_link_success(async_client, mock_db_session):
    """
    Тест успешного создания ссылки.
    """
    response = await async_client.post("/links/shorten", json={"original_url": "https://test.com"})

    assert response.status_code == 200
    data = response.json()
    assert data["original_url"] == "https://test.com"
    assert "short_code" in data


@pytest.mark.asyncio
async def test_create_short_link_custom_alias_invalid(async_client, mock_db_session):
    """
    Тест неудачного создания ссылки - использование ключевого слова `search`.
    """
    response = await async_client.post("/links/shorten", json={
        "original_url": "https://example.com",
        "custom_alias": "search"
    })

    assert response.status_code == 400
    assert "cannot be used" in response.text.lower()


@pytest.mark.asyncio
async def test_create_short_link_custom_alias_already_exists(async_client, mock_db_session):
    """
    Тест неудачного создания ссылки - алиас уже используется.
    """
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = MagicMock()

    response = await async_client.post("/links/shorten", json={
        "original_url": "https://example.com",
        "custom_alias": "alias"
    })

    assert response.status_code == 400
    assert "already in use" in response.text.lower()


@pytest.mark.asyncio
async def test_create_link_custom_alias_ok(async_client, mock_db_session):
    """
    Тест удачного создания ссылки по незанятому алиасу.
    """
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = None

    response = await async_client.post("/links/shorten", json={
        "original_url": "https://example.com",
        "custom_alias": "alias"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["short_code"] == "alias"


@pytest.mark.asyncio
async def test_search_links_by_original_success(async_client, mock_db_session):
    """
    Тест поиска ссылок по оригинальному url.
    """
    # Мок объекта ссылки
    fake_link = MagicMock(
        short_code = "abc123",
        original_url = "https://example.com"
    )
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [fake_link]

    response = await async_client.get("/links/search", params={"original_url": "https://example.com"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["short_code"] == "abc123"
    assert data[0]["original_url"] == "https://example.com"


@pytest.mark.asyncio
async def test_search_links_by_original_not_found(async_client, mock_db_session):
    """
    Тест поиска ссылок по оригинальному url, когда он не найден.
    """
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
    response = await async_client.get("/links/search", params={"original_url": "https://notfound.com"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_redirect_by_code_success(async_client, mock_db_session):
    """
    Тест успешного редиректа.
    """
    fake_link = MagicMock(
        short_code="abc123",
        original_url = "https://example.com",
        clicks_count = 0,
        last_clicked_at = None
    )
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = fake_link

    response = await async_client.get("links/abc123", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com"
    # Проверка обновления данных ссылки
    assert fake_link.clicks_count == 1
    assert fake_link.last_clicked_at is not None


@pytest.mark.asyncio
async def test_redirect_by_code_not_found(async_client, mock_db_session):
    """
    Тест редиректа, когда короткая ссылка не найдена.
    """
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = None
    response = await async_client.get("links/notfound")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_link_success(async_client, mock_db_session):
    """
    Тест изменения оригинального url по короткой ссылке.
    """
    fake_link = MagicMock(
        original_url = "https://old.com",
        user_id = 1,
        short_code = "abc123"
    )

    mock_db_session.execute.return_value.scalars.return_value.first.return_value = fake_link
    app.dependency_overrides[current_active_user] = lambda: MagicMock(id=1)

    response = await async_client.put(
        "/links/abc123",
        json={"original_url": "https://new.com"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["original_url"] == "https://new.com"
    assert fake_link.original_url == "https://new.com"

    app.dependency_overrides.pop(current_active_user, None)


@pytest.mark.asyncio
async def test_update_link_forbidden(async_client, mock_db_session):
    """
    Тест изменения оригинального url по короткой ссылке, когда у пользователя нет прав.
    """
    fake_link = MagicMock(original_url="https://old.com", user_id=1)
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = fake_link

    app.dependency_overrides[current_active_user] = lambda: MagicMock(id=2)

    response = await async_client.put(
        "/links/abc123",
        json={"original_url": "https://unauthorized.com"}
    )

    assert response.status_code == 403
    assert "no access" in response.text.lower()

    app.dependency_overrides.pop(current_active_user, None)


@pytest.mark.asyncio
async def test_update_link_not_found(async_client, mock_db_session):
    """
    Тест изменения оригинального url по короткой ссылке, когда она не найдена.
    """
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = None
    app.dependency_overrides[current_active_user] = lambda: MagicMock(id=1)

    response = await async_client.put(
        "/links/notfound",
        json={"original_url": "https://notfound.com"}
    )

    assert response.status_code == 404
    assert "not found" in response.text.lower()

    app.dependency_overrides.pop(current_active_user, None)


@pytest.mark.asyncio
async def test_delete_link_success(async_client, mock_db_session):
    """
    Тест успешного удаления ссылки.
    """
    fake_link = MagicMock(short_code = "test123", original_url="https://example.com", user_id=1)
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = fake_link
    app.dependency_overrides[current_active_user] = lambda: MagicMock(id=1)

    response = await async_client.delete("/links/test123")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "test123" in data["message"]

    app.dependency_overrides.pop(current_active_user, None)


@pytest.mark.asyncio
async def test_delete_link_forbidden(async_client, mock_db_session):
    """
    Тест неудачного удаления ссылки, когда у пользователя нет доступа.
    """
    fake_link = MagicMock(short_code = "abc123", original_url="https://example.com", user_id=1)
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = fake_link
    app.dependency_overrides[current_active_user] = lambda: MagicMock(id=2)

    response = await async_client.delete("/links/abc123")

    assert response.status_code == 403
    assert "no access" in response.text.lower()

    app.dependency_overrides.pop(current_active_user, None)


@pytest.mark.asyncio
async def test_delete_link_not_found(async_client, mock_db_session):
    """
    Тест неудачного удаления ссылки, когда она не найдена.
    """
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = None
    app.dependency_overrides[current_active_user] = lambda: MagicMock(id=1)

    response = await async_client.delete("/links/notfound")

    assert response.status_code == 404
    assert "not found" in response.text.lower()

    app.dependency_overrides.pop(current_active_user, None)


@pytest.mark.asyncio
async def test_get_stats_success(async_client, mock_db_session):
    """
    Тест получения статистики по ссылке.
    """
    fake_link = MagicMock(
        short_code="abc123",
        original_url="https://example.com",
        clicks_count=42,
        last_clicked_at=None
    )
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = fake_link

    response = await async_client.get("/links/abc123/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["clicks_count"] == 42
    assert data["original_url"] == "https://example.com"
    assert "short_code" in data


@pytest.mark.asyncio
async def test_get_stats_not_found(async_client, mock_db_session):
    """
    Тест получения статистики по ссылке, когда она не найдена.
    """
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = None

    response = await async_client.get("/links/notfound/stats")

    assert response.status_code == 404
    assert "not found" in response.text.lower()
