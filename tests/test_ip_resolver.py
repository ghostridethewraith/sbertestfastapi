from app.ip_resolver import resolve_client_ip


def test_resolver_uses_forwarded_header() -> None:
    headers = {"forwarded": "for=203.0.113.10;proto=https"}

    assert resolve_client_ip(headers, "10.0.0.9") == "203.0.113.10"


def test_resolver_uses_first_x_forwarded_for_ip() -> None:
    headers = {"x-forwarded-for": "198.51.100.1, 10.0.0.1"}

    assert resolve_client_ip(headers, "10.0.0.9") == "198.51.100.1"


def test_resolver_uses_x_real_ip() -> None:
    headers = {"x-real-ip": "192.0.2.15"}

    assert resolve_client_ip(headers, "10.0.0.9") == "192.0.2.15"


def test_resolver_falls_back_to_request_client() -> None:
    assert resolve_client_ip({}, "10.0.0.9") == "10.0.0.9"
