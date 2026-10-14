from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterator

import httpx


@dataclass(frozen=True)
class StreamEvent:
    event: str
    data: dict


class SilabsAIClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        client_id: str,
        timeout: float | None = 60.0,
    ) -> None:
        if not base_url:
            raise ValueError("base_url is required")
        if not api_key:
            raise ValueError("api_key is required")
        if not client_id:
            raise ValueError("client_id is required")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client_id = client_id
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "X-Silabs-Client": self.client_id,
            "X-Silabs-API-Key": self.api_key,
        }

    def _request(self, method: str, path: str, **kwargs) -> dict:
        response = httpx.request(
            method,
            self.base_url + path,
            headers={**self._headers(), **kwargs.pop("headers", {})},
            timeout=self.timeout,
            **kwargs,
        )
        response.raise_for_status()
        payload = response.json()
        request_id = response.headers.get("X-Request-ID")
        if request_id and isinstance(payload, dict) and "request_id" not in payload:
            payload["request_id"] = request_id
        return payload

    def chat(self, **payload) -> dict:
        return self._request("POST", "/v1/chat", json=payload)

    def generate(self, **payload) -> dict:
        return self._request("POST", "/v1/generate", json=payload)

    def usage(self) -> dict:
        return self._request("GET", "/v1/usage")

    def health(self) -> dict:
        return self._request("GET", "/v1/health")

    def stream_chat(self, **payload) -> Iterator[StreamEvent]:
        with httpx.stream(
            "POST",
            self.base_url + "/v1/chat/stream",
            headers={**self._headers(), "Accept": "text/event-stream"},
            json=payload,
            timeout=None,
        ) as response:
            response.raise_for_status()
            event = "message"
            data_lines: list[str] = []

            for raw_line in response.iter_lines():
                line = raw_line.rstrip("\r")
                if line == "":
                    if data_lines:
                        yield StreamEvent(
                            event=event,
                            data=json.loads("".join(data_lines)),
                        )
                    event = "message"
                    data_lines = []
                    continue

                if line.startswith("event:"):
                    event = line[6:].strip()
                elif line.startswith("data:"):
                    data_lines.append(line[5:].strip())

            if data_lines:
                yield StreamEvent(
                    event=event,
                    data=json.loads("".join(data_lines)),
                )
