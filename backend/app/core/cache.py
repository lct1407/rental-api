"""
Redis cache manager for caching and session management
"""
import json
from typing import Optional, Any, List
import redis.asyncio as aioredis
from redis.asyncio import Redis
from app.config import settings
import pickle


class RedisCache:
    """Redis cache manager"""

    _redis: Optional[Redis] = None

    @classmethod
    async def initialize(cls):
        """Initialize Redis connection"""
        if cls._redis is None:
            cls._redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                db=settings.REDIS_DB,
            )

    @classmethod
    async def close(cls):
        """Close Redis connection"""
        if cls._redis:
            await cls._redis.close()
            cls._redis = None

    @classmethod
    async def get_redis(cls) -> Redis:
        """Get Redis connection"""
        if cls._redis is None:
            await cls.initialize()
        return cls._redis

    # Basic Operations

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """Get value from cache"""
        redis = await cls.get_redis()
        value = await redis.get(key)
        if value:
            try:
                return pickle.loads(value)
            except Exception:
                return value.decode() if isinstance(value, bytes) else value
        return None

    @classmethod
    async def set(
        cls,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds
        """
        redis = await cls.get_redis()
        try:
            serialized = pickle.dumps(value)
        except Exception:
            serialized = str(value)

        if expire:
            return await redis.setex(key, expire, serialized)
        else:
            return await redis.set(key, serialized)

    @classmethod
    async def delete(cls, key: str) -> bool:
        """Delete key from cache"""
        redis = await cls.get_redis()
        return await redis.delete(key) > 0

    @classmethod
    async def exists(cls, key: str) -> bool:
        """Check if key exists"""
        redis = await cls.get_redis()
        return await redis.exists(key) > 0

    @classmethod
    async def expire(cls, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        redis = await cls.get_redis()
        return await redis.expire(key, seconds)

    @classmethod
    async def ttl(cls, key: str) -> int:
        """Get time to live for key"""
        redis = await cls.get_redis()
        return await redis.ttl(key)

    # JSON Operations

    @classmethod
    async def get_json(cls, key: str) -> Optional[dict]:
        """Get JSON value from cache"""
        redis = await cls.get_redis()
        value = await redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    @classmethod
    async def set_json(
        cls,
        key: str,
        value: dict,
        expire: Optional[int] = None
    ) -> bool:
        """Set JSON value in cache"""
        redis = await cls.get_redis()
        serialized = json.dumps(value)

        if expire:
            return await redis.setex(key, expire, serialized)
        else:
            return await redis.set(key, serialized)

    # List Operations

    @classmethod
    async def lpush(cls, key: str, *values: Any) -> int:
        """Push values to the left of list"""
        redis = await cls.get_redis()
        serialized = [pickle.dumps(v) for v in values]
        return await redis.lpush(key, *serialized)

    @classmethod
    async def rpush(cls, key: str, *values: Any) -> int:
        """Push values to the right of list"""
        redis = await cls.get_redis()
        serialized = [pickle.dumps(v) for v in values]
        return await redis.rpush(key, *serialized)

    @classmethod
    async def lrange(cls, key: str, start: int, end: int) -> List[Any]:
        """Get range of list"""
        redis = await cls.get_redis()
        values = await redis.lrange(key, start, end)
        return [pickle.loads(v) for v in values]

    @classmethod
    async def llen(cls, key: str) -> int:
        """Get length of list"""
        redis = await cls.get_redis()
        return await redis.llen(key)

    # Set Operations

    @classmethod
    async def sadd(cls, key: str, *values: Any) -> int:
        """Add values to set"""
        redis = await cls.get_redis()
        serialized = [pickle.dumps(v) for v in values]
        return await redis.sadd(key, *serialized)

    @classmethod
    async def smembers(cls, key: str) -> set:
        """Get all members of set"""
        redis = await cls.get_redis()
        values = await redis.smembers(key)
        return {pickle.loads(v) for v in values}

    @classmethod
    async def sismember(cls, key: str, value: Any) -> bool:
        """Check if value is member of set"""
        redis = await cls.get_redis()
        serialized = pickle.dumps(value)
        return await redis.sismember(key, serialized)

    # Hash Operations

    @classmethod
    async def hset(cls, key: str, field: str, value: Any) -> int:
        """Set hash field"""
        redis = await cls.get_redis()
        serialized = pickle.dumps(value)
        return await redis.hset(key, field, serialized)

    @classmethod
    async def hget(cls, key: str, field: str) -> Optional[Any]:
        """Get hash field"""
        redis = await cls.get_redis()
        value = await redis.hget(key, field)
        if value:
            return pickle.loads(value)
        return None

    @classmethod
    async def hgetall(cls, key: str) -> dict:
        """Get all hash fields"""
        redis = await cls.get_redis()
        data = await redis.hgetall(key)
        return {
            k.decode() if isinstance(k, bytes) else k: pickle.loads(v)
            for k, v in data.items()
        }

    @classmethod
    async def hdel(cls, key: str, *fields: str) -> int:
        """Delete hash fields"""
        redis = await cls.get_redis()
        return await redis.hdel(key, *fields)

    # Increment/Decrement

    @classmethod
    async def incr(cls, key: str, amount: int = 1) -> int:
        """Increment value"""
        redis = await cls.get_redis()
        return await redis.incrby(key, amount)

    @classmethod
    async def decr(cls, key: str, amount: int = 1) -> int:
        """Decrement value"""
        redis = await cls.get_redis()
        return await redis.decrby(key, amount)

    # Pattern Operations

    @classmethod
    async def keys(cls, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        redis = await cls.get_redis()
        keys = await redis.keys(pattern)
        return [k.decode() if isinstance(k, bytes) else k for k in keys]

    @classmethod
    async def delete_pattern(cls, pattern: str) -> int:
        """Delete all keys matching pattern"""
        redis = await cls.get_redis()
        keys = await redis.keys(pattern)
        if keys:
            return await redis.delete(*keys)
        return 0

    # Pub/Sub

    @classmethod
    async def publish(cls, channel: str, message: Any) -> int:
        """Publish message to channel"""
        redis = await cls.get_redis()
        serialized = pickle.dumps(message)
        return await redis.publish(channel, serialized)

    @classmethod
    async def subscribe(cls, *channels: str):
        """Subscribe to channels"""
        redis = await cls.get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub

    # Utility Methods

    @classmethod
    async def ping(cls) -> bool:
        """Ping Redis server"""
        try:
            redis = await cls.get_redis()
            return await redis.ping()
        except Exception:
            return False

    @classmethod
    async def flush(cls):
        """Flush current database"""
        redis = await cls.get_redis()
        await redis.flushdb()

    @classmethod
    async def info(cls) -> dict:
        """Get Redis server info"""
        redis = await cls.get_redis()
        return await redis.info()


# Cache decorators

def cache(
    key_prefix: str,
    expire: int = 3600,
    key_builder: Optional[callable] = None
):
    """
    Decorator to cache function results

    Usage:
        @cache(key_prefix="user", expire=3600)
        async def get_user(user_id: int):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = f"{key_prefix}:{key_builder(*args, **kwargs)}"
            else:
                # Simple key building
                key_parts = [str(arg) for arg in args] + [
                    f"{k}={v}" for k, v in kwargs.items()
                ]
                cache_key = f"{key_prefix}:{':'.join(key_parts)}"

            # Try to get from cache
            cached = await RedisCache.get(cache_key)
            if cached is not None:
                return cached

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await RedisCache.set(cache_key, result, expire=expire)

            return result

        return wrapper
    return decorator


def invalidate_cache(key_prefix: str, key_builder: Optional[callable] = None):
    """
    Decorator to invalidate cache after function execution

    Usage:
        @invalidate_cache(key_prefix="user")
        async def update_user(user_id: int):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Execute function
            result = await func(*args, **kwargs)

            # Invalidate cache
            if key_builder:
                cache_key = f"{key_prefix}:{key_builder(*args, **kwargs)}"
            else:
                # Delete all keys with prefix
                await RedisCache.delete_pattern(f"{key_prefix}:*")

            await RedisCache.delete(cache_key)

            return result

        return wrapper
    return decorator
