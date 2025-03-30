from redis.asyncio import Redis
from urllib.parse import urlencode
import json
from src.logger_config import logger


_redis_client = None


def get_redis_client() -> Redis:
    """
    Возвращает Redis-клиент. Инициализирует его один раз (лениво).
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(
            host="redis",
            port=6379,
            password=None,
            decode_responses=True,
        )
    return _redis_client


def build_cache_key(path: str, query_params: dict) -> str:
    """
    Шаблон формирования ключа.
    """
    query_string = urlencode(query_params)
    return f"{path}?{query_string}"


async def cache_set(path: str, query_params: dict, data: dict, expire: int = 300):
    """
    Создание кэша.
    """
    key = build_cache_key(path, query_params)
    value = json.dumps(data, default=str)
    await get_redis_client().set(key, value, ex=expire)


async def cache_get(path: str, query_params: dict):
    """
    Получение кэша.
    """
    key = build_cache_key(path, query_params)
    cached = await get_redis_client().get(key)
    return json.loads(cached) if cached else None


async def cache_delete(path: str, query_params: dict):
    """
    Удаление кэша.
    """
    key = build_cache_key(path, query_params)
    logger.info(f"Key = {key}")
    await get_redis_client().delete(key)