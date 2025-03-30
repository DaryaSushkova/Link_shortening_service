import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.tasks.cleanup_links import delete_expired_links, delete_unused_links


@pytest.mark.asyncio
@patch("src.tasks.cleanup_links.async_session_maker")
async def test_delete_expired_links(mock_session_maker):
    """
    Тест шедулера, удаляющего истекшие по сроку жизни ссылки.
    """
    mock_session = AsyncMock()
    mock_execute_result = MagicMock()
    mock_execute_result.fetchall = AsyncMock(return_value=[(1,), (2,)])
    mock_session.execute = AsyncMock(return_value=mock_execute_result)
    mock_session_maker.return_value.__aenter__.return_value = mock_session

    await delete_expired_links()

    mock_session.execute.assert_awaited()
    mock_execute_result.fetchall.assert_awaited()
    mock_session.commit.assert_awaited()


@pytest.mark.asyncio
@patch("src.tasks.cleanup_links.async_session_maker")
async def test_delete_unused_links(mock_session_maker):
    """
    Тест шедулера, удаляющего неиспользуемые ссылки.
    """
    mock_session = AsyncMock()
    mock_execute_result = MagicMock()
    mock_execute_result.fetchall = AsyncMock(return_value=[(10,), (20,)])
    mock_session.execute = AsyncMock(return_value=mock_execute_result)
    mock_session_maker.return_value.__aenter__.return_value = mock_session

    await delete_unused_links()

    mock_session.execute.assert_awaited()
    mock_execute_result.fetchall.assert_awaited()
    mock_session.commit.assert_awaited()
