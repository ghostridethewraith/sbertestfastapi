import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes import get_ip_service
from app.service import IpService
from app.storage import ComputerIpStorage


@pytest.fixture
def fake_storage() -> ComputerIpStorage:
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    return ComputerIpStorage(redis_client, ttl_seconds=60)


@pytest.fixture
def client(fake_storage: ComputerIpStorage) -> TestClient:
    app.dependency_overrides[get_ip_service] = lambda: IpService(fake_storage)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_api_returns_ip_without_saving(client: TestClient) -> None:
    response = client.get("/", headers={"x-real-ip": "192.0.2.10"})

    assert response.status_code == 200
    assert response.json() == {
        "ip": "192.0.2.10",
        "computer_name": None,
        "saved": False,
    }


def test_api_saves_computer_name_binding(
    client: TestClient,
    fake_storage: ComputerIpStorage,
) -> None:
    response = client.get(
        "/",
        params={"computer_name": "my-pc"},
        headers={"x-real-ip": "192.0.2.20"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "ip": "192.0.2.20",
        "computer_name": "my-pc",
        "saved": True,
    }
    assert fake_storage.get("my-pc") == "192.0.2.20"


def test_api_uses_computer_name_header_when_query_param_is_missing(
    client: TestClient,
    fake_storage: ComputerIpStorage,
) -> None:
    response = client.get(
        "/",
        headers={
            "x-real-ip": "192.0.2.30",
            "x-computer-name": "header-pc",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "ip": "192.0.2.30",
        "computer_name": "header-pc",
        "saved": True,
    }
    assert fake_storage.get("header-pc") == "192.0.2.30"


def test_api_query_param_has_priority_over_computer_name_header(
    client: TestClient,
    fake_storage: ComputerIpStorage,
) -> None:
    response = client.get(
        "/",
        params={"computer_name": "query-pc"},
        headers={
            "x-real-ip": "192.0.2.40",
            "x-computer-name": "header-pc",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "ip": "192.0.2.40",
        "computer_name": "query-pc",
        "saved": True,
    }
    assert fake_storage.get("query-pc") == "192.0.2.40"
    assert fake_storage.get("header-pc") is None


def test_healthz() -> None:
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
