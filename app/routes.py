from ipaddress import ip_address

from fastapi import APIRouter, Depends, Query, Request

from app.models import IpResponse
from app.storage import ComputerIpStorage, create_storage

router = APIRouter()


def _clean_ip(raw_value: str | None) -> str | None:
    if not raw_value:
        return None

    value = raw_value.strip().strip('"').strip("'")
    if not value:
        return None

    if value.startswith("[") and "]" in value:
        value = value[1 : value.index("]")]
    elif ":" in value and value.count(":") == 1:
        host, port = value.rsplit(":", 1)
        if port.isdigit():
            value = host

    try:
        ip_address(value)
    except ValueError:
        return None
    return value


def _extract_forwarded_ip(forwarded_header: str | None) -> str | None:
    if not forwarded_header:
        return None

    for forwarded_part in forwarded_header.split(","):
        for pair in forwarded_part.split(";"):
            name, separator, value = pair.strip().partition("=")
            if separator and name.lower() == "for":
                parsed = _clean_ip(value)
                if parsed:
                    return parsed
    return None


def get_client_ip(request: Request) -> str:
    forwarded_ip = _extract_forwarded_ip(request.headers.get("forwarded"))
    if forwarded_ip:
        return forwarded_ip

    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        for candidate in x_forwarded_for.split(","):
            parsed = _clean_ip(candidate)
            if parsed:
                return parsed

    real_ip = _clean_ip(request.headers.get("x-real-ip"))
    if real_ip:
        return real_ip

    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@router.get("/", response_model=IpResponse)
def read_ip(
    request: Request,
    computer_name: str | None = Query(default=None, min_length=1),
    storage: ComputerIpStorage = Depends(create_storage),
) -> IpResponse:
    client_ip = get_client_ip(request)
    resolved_computer_name = computer_name or request.headers.get("x-computer-name")
    saved = False

    if resolved_computer_name:
        storage.save(resolved_computer_name, client_ip)
        saved = True

    return IpResponse(ip=client_ip, computer_name=resolved_computer_name, saved=saved)


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
