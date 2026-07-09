import os
from typing import Protocol

from redis import Redis


DEFAULT_REDIS_URL = "redis://redis:6379/0"
DEFAULT_TTL_SECONDS = 300


class KeyValueStore(Protocol):
    def setex(self, name: str, time: int, value: str) -> object:
        ...

    def get(self, name: str) -> object:
        ...

    def ttl(self, name: str) -> int:
        ...


class ComputerIpStorage:
    def __init__(self, redis_client: KeyValueStore, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def key(computer_name: str) -> str:
        return f"computer:{computer_name}"

    def save(self, computer_name: str, ip_address: str) -> None:
        self.redis_client.setex(self.key(computer_name), self.ttl_seconds, ip_address)

    def get(self, computer_name: str) -> str | None:
        value = self.redis_client.get(self.key(computer_name))
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)

    def ttl(self, computer_name: str) -> int:
        return self.redis_client.ttl(self.key(computer_name))


def get_ttl_seconds() -> int:
    raw_ttl = os.getenv("BINDING_TTL_SECONDS", str(DEFAULT_TTL_SECONDS))
    try:
        ttl = int(raw_ttl)
    except ValueError:
        return DEFAULT_TTL_SECONDS
    return ttl if ttl > 0 else DEFAULT_TTL_SECONDS


def create_storage() -> ComputerIpStorage:
    redis_url = os.getenv("REDIS_URL", DEFAULT_REDIS_URL)
    redis_client = Redis.from_url(redis_url, decode_responses=True)
    return ComputerIpStorage(redis_client, get_ttl_seconds())
