import fakeredis
from fastapi.testclient import TestClient

from app.main import app
from app.routes import create_storage, get_client_ip
from app.storage import ComputerIpStorage


class DummyClient:
    host = "10.0.0.9"


class DummyRequest:
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = headers or {}
        self.client = DummyClient()


def test_get_client_ip_uses_forwarded_header() -> None:
    request = DummyRequest({"forwarded": "for=203.0.113.10;proto=https"})

    assert get_client_ip(request) == "203.0.113.10"


def test_get_client_ip_uses_first_x_forwarded_for_ip() -> None:
    request = DummyRequest({"x-forwarded-for": "198.51.100.1, 10.0.0.1"})

    assert get_client_ip(request) == "198.51.100.1"


def test_get_client_ip_uses_x_real_ip() -> None:
    request = DummyRequest({"x-real-ip": "192.0.2.15"})

    assert get_client_ip(request) == "192.0.2.15"


def test_get_client_ip_falls_back_to_request_client() -> None:
    request = DummyRequest()

    assert get_client_ip(request) == "10.0.0.9"


def test_api_returns_ip_without_saving() -> None:
    client = TestClient(app)

    response = client.get("/", headers={"x-real-ip": "192.0.2.10"})

    assert response.status_code == 200
    assert response.json() == {
        "ip": "192.0.2.10",
        "computer_name": None,
        "saved": False,
    }


def test_api_saves_computer_name_binding() -> None:
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    storage = ComputerIpStorage(redis_client, ttl_seconds=60)
    app.dependency_overrides[create_storage] = lambda: storage
    client = TestClient(app)

    try:
        response = client.get(
            "/",
            params={"computer_name": "my-pc"},
            headers={"x-real-ip": "192.0.2.20"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "ip": "192.0.2.20",
        "computer_name": "my-pc",
        "saved": True,
    }
    assert storage.get("my-pc") == "192.0.2.20"


def test_api_uses_computer_name_header_when_query_param_is_missing() -> None:
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    storage = ComputerIpStorage(redis_client, ttl_seconds=60)
    app.dependency_overrides[create_storage] = lambda: storage
    client = TestClient(app)

    try:
        response = client.get(
            "/",
            headers={
                "x-real-ip": "192.0.2.30",
                "x-computer-name": "header-pc",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "ip": "192.0.2.30",
        "computer_name": "header-pc",
        "saved": True,
    }
    assert storage.get("header-pc") == "192.0.2.30"


def test_api_query_param_has_priority_over_computer_name_header() -> None:
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    storage = ComputerIpStorage(redis_client, ttl_seconds=60)
    app.dependency_overrides[create_storage] = lambda: storage
    client = TestClient(app)

    try:
        response = client.get(
            "/",
            params={"computer_name": "query-pc"},
            headers={
                "x-real-ip": "192.0.2.40",
                "x-computer-name": "header-pc",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "ip": "192.0.2.40",
        "computer_name": "query-pc",
        "saved": True,
    }
    assert storage.get("query-pc") == "192.0.2.40"
    assert storage.get("header-pc") is None


def test_healthz() -> None:
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
