from ipaddress import ip_address
from typing import Mapping


def clean_ip(raw_value: str | None) -> str | None:
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


def extract_forwarded_ip(forwarded_header: str | None) -> str | None:
    if not forwarded_header:
        return None

    for forwarded_part in forwarded_header.split(","):
        for pair in forwarded_part.split(";"):
            name, separator, value = pair.strip().partition("=")
            if separator and name.lower() == "for":
                parsed = clean_ip(value)
                if parsed:
                    return parsed
    return None


def resolve_client_ip(headers: Mapping[str, str], client_host: str | None) -> str:
    forwarded_ip = extract_forwarded_ip(headers.get("forwarded"))
    if forwarded_ip:
        return forwarded_ip

    x_forwarded_for = headers.get("x-forwarded-for")
    if x_forwarded_for:
        for candidate in x_forwarded_for.split(","):
            parsed = clean_ip(candidate)
            if parsed:
                return parsed

    real_ip = clean_ip(headers.get("x-real-ip"))
    if real_ip:
        return real_ip

    return client_host or "unknown"
