from fastapi import APIRouter, Depends, Query, Request

from app.models import IpResponse
from app.service import IpService, create_ip_service
from app.storage import ComputerIpStorage, create_storage

router = APIRouter()


def get_ip_service(storage: ComputerIpStorage = Depends(create_storage)) -> IpService:
    return create_ip_service(storage)


@router.get("/", response_model=IpResponse)
def read_ip(
    request: Request,
    computer_name: str | None = Query(default=None, min_length=1),
    service: IpService = Depends(get_ip_service),
) -> IpResponse:
    client_host = request.client.host if request.client else None
    return service.handle_request(request.headers, client_host, computer_name)


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
