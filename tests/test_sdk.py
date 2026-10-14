from clients.python.silabs_ai_client import SilabsAIClient


def test_python_client_requires_credentials():
    try:
        SilabsAIClient(base_url="http://localhost", api_key="", client_id="unixpress")
    except ValueError as exc:
        assert "api_key" in str(exc)
    else:
        raise AssertionError("Expected missing API key to fail")


def test_python_client_builds_auth_headers():
    client = SilabsAIClient(
        base_url="http://localhost:8000/",
        api_key="secret",
        client_id="unixpress",
    )

    assert client.base_url == "http://localhost:8000"
    assert client._headers() == {
        "X-Silabs-Client": "unixpress",
        "X-Silabs-API-Key": "secret",
    }
