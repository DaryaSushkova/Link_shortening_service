import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse
from sqlalchemy import select

from src.database import get_async_session
from src.auth.manager import optional_user, current_active_user
from src.auth.models import User
from src.links.models import ShortLink
from src.utils.shortcode import generate_short_code_from_uuid
from src.links.schemas import LinkCreate, LinkRead, LinkStats, LinkUpdate
from src.cache.redis_client import cache_get, cache_set, cache_delete


router = APIRouter()


@router.post("/shorten", response_model=LinkRead)
async def create_short_link(
    link_data: LinkCreate,
    session: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(optional_user),  
):
    """
    Создание короткой ссылки.
    """

    link_id = uuid.uuid4()

    # Указана кастомная ссылка
    if link_data.custom_alias:
        if link_data.custom_alias == 'search':
            raise HTTPException(status_code=400, detail=f"Custom alias '{link_data.custom_alias}' cannot be used!")
        # Проверка на уникальность
        stmt = select(ShortLink).where(ShortLink.short_code == link_data.custom_alias)
        result = await session.execute(stmt)
        exiting_alias = result.scalars().first()

        if exiting_alias:
            raise HTTPException(status_code=400, detail=f"Custom alias '{link_data.custom_alias}' is already in use!")
        
        short_code = link_data.custom_alias
    else:
        while True:
            short_code = generate_short_code_from_uuid(link_id)
            stmt = select(ShortLink).where(ShortLink.short_code == short_code)
            result = await session.execute(stmt)
            existing = result.scalars().first()
            if not existing:
                break

    # Если анонимный пользователь, то задаем время жизни ссылки на 1 день
    if not user and not link_data.expires_at:
        link_data.expires_at = datetime.now(timezone.utc) + timedelta(days=1)

    # Если пользователь авторизован, записывается user_id,
    # иначе None - ссылка "анонимная"
    new_link = ShortLink(
        id=link_id,
        short_code=short_code,
        original_url=link_data.original_url,
        user_id=user.id if user else None,
        expires_at=link_data.expires_at
    )
    session.add(new_link)
    await session.commit()
    await session.refresh(new_link)

    # Удаление кэша
    await cache_delete(f"/links/search", {"original_url": link_data.original_url})

    return LinkRead(
        short_code=new_link.short_code,
        original_url=new_link.original_url,
    )


@router.get("/search", response_model=List[LinkRead])
async def search_links_by_original(
    request: Request,
    original_url: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Поиск коротких ссылок по оригинальному URL.
    """

    # Поиск кэша
    cached = await cache_get(request.url.path, {"original_url": original_url})
    if cached:
        return cached
    
    stmt = select(ShortLink).where(ShortLink.original_url == original_url)
    result = await session.execute(stmt)
    links = result.scalars().all()

    if not links:
        raise HTTPException(status_code=404, detail="Original link not found!")
    
    # Кэширование
    response = [LinkRead.model_validate(link) for link in links]
    await cache_set(request.url.path, {"original_url": original_url}, response)
    
    return links


@router.get("/{short_code}")
async def redirect_by_code(
    request: Request,
    short_code: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Поиск короткой ссылки и редирект. 
    """

    # Поиск кэша
    cached = await cache_get(request.url.path, {})
    if cached:
        return cached

    # Получение объекта по короткой ссылке
    stmt = select(ShortLink).where(ShortLink.short_code == short_code)
    result = await session.execute(stmt)
    link = result.scalars().first()

    # Короткая ссылка не найдена
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found!")
    
    await cache_set(request.url.path, {}, link.original_url, expire=60)
    
    # Обновление данных связи и удаление кэша
    link.clicks_count += 1
    link.last_clicked_at = datetime.now(timezone.utc)
    await session.commit()
    await cache_delete(f"/links/{short_code}/stats", {})

    return RedirectResponse(url=link.original_url, status_code=302)


@router.put("/{short_code}", response_model=LinkRead)
async def update_link(
    short_code: str,
    link_data: LinkUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Обновление исходного URL по короткому коду.
    """

    stmt = select(ShortLink).where(ShortLink.short_code == short_code)
    result = await session.execute(stmt)
    link = result.scalars().first()

    if not link:
        raise HTTPException(status_code=404, detail="Short link not found!")

    # Обновлять можно только свои ссылки
    if link.user_id is None or link.user_id != user.id:
        raise HTTPException(status_code=403, detail="You have no access to this link!")

    # Обновление исходного URL
    previous_url = link.original_url
    link.original_url = link_data.original_url
    await session.commit()
    await session.refresh(link)

    # Удаление кэша
    await cache_delete(f"/links/search", {"original_url": previous_url})
    await cache_delete(f"/links/search", {"original_url": link_data.original_url})
    await cache_delete(f"/links/{short_code}", {})
    await cache_delete(f"/links/{short_code}/stats", {})

    return LinkRead.model_validate(link)


@router.delete("/{short_code}")
async def delete_link(
    short_code: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Удаление короткой ссылки.
    """

    stmt = select(ShortLink).where(ShortLink.short_code == short_code)
    result = await session.execute(stmt)
    link = result.scalars().first()

    # Короткая ссылка не найдена
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found!")
    
    # Удалять можно только свои ссылки
    if link.user_id is None or link.user_id != user.id:
        raise HTTPException(status_code=403, detail="You have no access to this link!")

    # Удаление связи
    await session.delete(link)
    await session.commit()

    # Удаление кэша
    await cache_delete(f"/links/search", {"original_url": link.original_url})
    await cache_delete(f"/links/{short_code}", {})
    await cache_delete(f"/links/{short_code}/stats", {})

    return {"status": "success", "message": f"Short link '{short_code}' has been deleted"}


@router.get("/{short_code}/stats", response_model=LinkStats)
async def get_short_link_stats(
    request: Request,
    short_code: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получение статистики по ссылке.
    """

    # Поиск кэша
    cached = await cache_get(request.url.path, {})
    if cached:
        return cached
    
    # Находим объект по короткой ссылке
    stmt = select(ShortLink).where(ShortLink.short_code == short_code)
    result = await session.execute(stmt)
    link = result.scalars().first()

    # Короткая ссылка не найдена
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found!")
    
    await cache_set(request.url.path, {}, LinkStats.model_validate(link), expire=60)

    return link