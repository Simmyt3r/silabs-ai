from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from .config import Settings, get_settings


@dataclass(frozen=True)
class APIPrincipal:
    client_id: str


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def verify_api_key(
    raw_key: str,
    expected_hash: str,
) -> bool:
    candidate = hash_api_key(raw_key)
    return hmac.compare_digest(candidate, expected_hash.lower())


def authenticate_api_key(
    x_silabs_api_key: str | None,
    x_silabs_client: str | None,
    settings: Settings,
) -> APIPrincipal:
    if not settings.api_auth_enabled:
        return APIPrincipal(client_id=x_silabs_client or "development")

    client_id = (x_silabs_client or "").strip()
    raw_key = (x_silabs_api_key or "").strip()

    if not client_id or not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Silabs API credentials.",
            headers={"WWW-Authenticate": "SilabsApiKey"},
        )

    expected_hash = settings.api_key_hashes.get(client_id)
    if not expected_hash or not verify_api_key(raw_key, expected_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Silabs API credentials.",
            headers={"WWW-Authenticate": "SilabsApiKey"},
        )

    return APIPrincipal(client_id=client_id)


def require_api_key(
    x_silabs_api_key: str | None = Header(default=None, alias="X-Silabs-API-Key"),
    x_silabs_client: str | None = Header(default=None, alias="X-Silabs-Client"),
) -> APIPrincipal:
    return authenticate_api_key(
        x_silabs_api_key=x_silabs_api_key,
        x_silabs_client=x_silabs_client,
        settings=get_settings(),
    )
