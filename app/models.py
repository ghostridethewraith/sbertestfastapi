from pydantic import BaseModel


class IpResponse(BaseModel):
    ip: str
    computer_name: str | None = None
    saved: bool = False
