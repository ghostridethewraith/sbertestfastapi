import fakeredis

from app.storage import ComputerIpStorage, DEFAULT_TTL_SECONDS, get_ttl_seconds


def test_storage_saves_ip_with_ttl() -> None:
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    storage = ComputerIpStorage(redis_client, ttl_seconds=120)

    storage.save("workstation-1", "203.0.113.55")

    assert storage.get("workstation-1") == "203.0.113.55"
    assert 0 < storage.ttl("workstation-1") <= 120


def test_storage_returns_none_for_missing_binding() -> None:
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    storage = ComputerIpStorage(redis_client)

    assert storage.get("missing") is None


def test_invalid_ttl_env_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setenv("BINDING_TTL_SECONDS", "invalid")

    assert get_ttl_seconds() == DEFAULT_TTL_SECONDS


def test_non_positive_ttl_env_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setenv("BINDING_TTL_SECONDS", "0")

    assert get_ttl_seconds() == DEFAULT_TTL_SECONDS
