from datetime import datetime, timezone, timedelta
from sqlalchemy import delete, or_
from src.database import async_session_maker
from src.links.models import ShortLink
from src.logger_config import logger
from src.config import LINK_LIFETIME_DAYS


async def delete_expired_links():
    """
    Удаление истекших по expires_at ссылок.
    """

    logger.info("The cleanup of expired links is running...")

    async with async_session_maker() as session:
        stmt = delete(ShortLink).where(
            ShortLink.expires_at.is_not(None),
            ShortLink.expires_at < datetime.now(timezone.utc)
            ).returning(ShortLink.id)
        
        result = await session.execute(stmt)
        rows = result.fetchall()
        await session.commit()

        deleted_links = [row[0] for row in rows]
        logger.info(f"Deleted {len(deleted_links)} expired links")

    logger.info("The cleanup is ended!")


async def delete_unused_links():
    """
    Удаление неиспользуемых ссылок.
    """

    logger.info("The cleanup of unused links is running...")
    days_tthreshold = datetime.now(timezone.utc) - timedelta(days=LINK_LIFETIME_DAYS)

    async with async_session_maker() as session:
        stmt = delete(ShortLink).where(
            or_(ShortLink.last_clicked_at.is_(None),
                ShortLink.last_clicked_at < days_tthreshold)
            ).returning(ShortLink.id)
        
        result = await session.execute(stmt)
        rows = result.fetchall()
        await session.commit()

        deleted_links = [row[0] for row in rows]
        logger.info(f"Deleted {len(deleted_links)} unused links")

    logger.info("The cleanup is ended!")