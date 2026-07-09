from typing import Mapping

from app.ip_resolver import resolve_client_ip
from app.models import IpResponse
from app.storage import ComputerIpStorage


COMPUTER_NAME_HEADER = "x-computer-name"


class IpService:
    def __init__(self, storage: ComputerIpStorage) -> None:
        self.storage = storage

    def handle_request(
        self,
        headers: Mapping[str, str],
        client_host: str | None,
        computer_name: str | None = None,
    ) -> IpResponse:
        client_ip = resolve_client_ip(headers, client_host)
        resolved_computer_name = computer_name or headers.get(COMPUTER_NAME_HEADER)

        if not resolved_computer_name:
            return IpResponse(ip=client_ip)

        self.storage.save(resolved_computer_name, client_ip)
        return IpResponse(ip=client_ip, computer_name=resolved_computer_name, saved=True)


def create_ip_service(storage: ComputerIpStorage) -> IpService:
    return IpService(storage)
