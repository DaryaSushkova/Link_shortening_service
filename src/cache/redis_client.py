from redis.asyncio import Redis
from urllib.parse import urlencode
import json
from src.logger_config import logger


redis_client = Redis(
    host="redis",
    port=6379,
    password=None,
    decode_responses=True)


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
    await redis_client.set(key, value, ex=expire)


async def cache_get(path: str, query_params: dict):
    """
    Получение кэша.
    """
    key = build_cache_key(path, query_params)
    cached = await redis_client.get(key)
    return json.loads(cached) if cached else None


async def cache_delete(path: str, query_params: dict):
    """
    Удаление кэша.
    """
    key = build_cache_key(path, query_params)
    logger.info(f"Key = {key}")
    await redis_client.delete(key)