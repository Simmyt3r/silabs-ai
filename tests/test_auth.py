from fastapi import HTTPException

from silabs_ai.auth import hash_api_key, require_api_key, verify_api_key
from silabs_ai.config import Settings


def test_hash_and_verify_api_key():
    raw = "silabs_test_secret"
    digest = hash_api_key(raw)

    assert len(digest) == 64
    assert verify_api_key(raw, digest) is True
    assert verify_api_key("wrong", digest) is False


def test_auth_disabled_allows_development_client():
    settings = Settings(
        _env_file=None,
        api_auth_enabled=False,
    )

    principal = require_api_key(
        x_silabs_api_key=None,
        x_silabs_client=None,
        settings=settings,
    )

    assert principal.client_id == "development"


def test_auth_enabled_accepts_valid_product_key():
    raw = "silabs_valid_product_key"
    settings = Settings(
        _env_file=None,
        api_auth_enabled=True,
        api_key_hashes={"unixpress": hash_api_key(raw)},
    )

    principal = require_api_key(
        x_silabs_api_key=raw,
        x_silabs_client="unixpress",
        settings=settings,
    )

    assert principal.client_id == "unixpress"


def test_auth_enabled_rejects_missing_credentials():
    settings = Settings(
        _env_file=None,
        api_auth_enabled=True,
        api_key_hashes={"unixpress": hash_api_key("secret")},
    )

    try:
        require_api_key(
            x_silabs_api_key=None,
            x_silabs_client=None,
            settings=settings,
        )
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("Expected missing credentials to be rejected")


def test_auth_enabled_rejects_wrong_product_key():
    settings = Settings(
        _env_file=None,
        api_auth_enabled=True,
        api_key_hashes={"unixpress": hash_api_key("correct")},
    )

    try:
        require_api_key(
            x_silabs_api_key="wrong",
            x_silabs_client="unixpress",
            settings=settings,
        )
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("Expected invalid credentials to be rejected")
