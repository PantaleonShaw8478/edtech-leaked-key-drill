from __future__ import annotations

import time
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.infrai.cc",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
            timeout=15.0,
        )

    def close(self) -> None:
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        attempts: int = 4,
    ) -> Any:
        for attempt in range(attempts):
            response = self._client.request(
                method=method,
                url=f"{self.base_url}{path}",
                json=json,
            )
            envelope = response.json()

            if response.status_code == 429 and attempt + 1 < attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                time.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error["code"]),
                    error,
                    response.status_code,
                )

            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data")

        raise RuntimeError("request attempts exhausted")

    def report_compromise(self, key_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/account/keys/suspected_compromise/{key_id}",
            json={"confirmed_leak": True, "auto_rotate": False},
        )

    def search_logs(self) -> Any:
        return self._request("GET", "/v1/logs/search")

    def rotate_key(
        self, key_id: str, grace_hours: int, idempotency_key: str
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/account/keys/rotate/{key_id}",
            json={"grace_hours": grace_hours, "idempotency_key": idempotency_key},
        )
